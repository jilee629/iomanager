import re
from datetime import date, datetime, time, timedelta
from django.db import IntegrityError, transaction

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db.models import Exists, OuterRef, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone

from .models import (
    Customer,
    CustomerPass,
    PassTemplate,
    PassTransaction,
    ProductTemplate,
    SystemSetting,
    VisitOrderItem,
    VisitSession,
)

PAGE_SIZE_CHOICES = (10, 20, 50, 100)


def _record_expired_pass_transactions(today):
    """
    Best-effort guard: if scheduled expire job was skipped, record missing
    expired transactions when managers open related pages.
    """
    target_ids = list(
        CustomerPass.objects.filter(remaining_count__gt=0, expires_on__lte=today).values_list("id", flat=True)
    )
    for pass_id in target_ids:
        with transaction.atomic():
            customer_pass = (
                CustomerPass.objects.select_for_update()
                .select_related("customer", "template")
                .filter(id=pass_id, remaining_count__gt=0, expires_on__lte=today)
                .first()
            )
            if not customer_pass:
                continue

            if PassTransaction.objects.filter(
                customer_pass=customer_pass,
                status=PassTransaction.Status.EXPIRED,
            ).exists():
                continue

            remaining = customer_pass.remaining_count
            PassTransaction.objects.create(
                customer=customer_pass.customer,
                template=customer_pass.template,
                template_name_snapshot=customer_pass.template.name,
                quantity=remaining,
                status=PassTransaction.Status.EXPIRED,
                customer_pass=customer_pass,
            )
            customer_pass.remaining_count = 0
            customer_pass.save(update_fields=["remaining_count"])


def _get_system_setting():
    setting = SystemSetting.objects.order_by("id").first()
    if setting:
        return setting
    return SystemSetting.objects.create()


def _today_bounds():
    today = timezone.localdate()
    start = timezone.make_aware(datetime.combine(today, time.min))
    end = start + timedelta(days=1)
    return today, start, end


class IomanagerLoginView(LoginView):
    template_name = "iomanager_app/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("iomanager_app:selection")


def root_redirect(request):
    if request.user.is_authenticated:
        return redirect("iomanager_app:selection")
    return redirect("iomanager_app:login")


@login_required
def selection_view(request):
    return render(request, "iomanager_app/selection.html")


@login_required
def customer_home_view(request):
    if request.method == "POST":
        raw_phone = request.POST.get("phone_number", "")
        phone_number = re.sub(r"\D", "", raw_phone)

        if len(phone_number) != 11:
            return redirect("iomanager_app:customer_home")

        _, start_of_day, end_of_day = _today_bounds()

        with transaction.atomic():
            try:
                customer, _ = Customer.objects.get_or_create(phone_number=phone_number)
            except IntegrityError:
                customer = Customer.objects.get(phone_number=phone_number)

            customer = Customer.objects.select_for_update().get(pk=customer.pk)
            active_visit = (
                VisitSession.objects.select_for_update()
                .filter(
                    customer=customer,
                    requested_at__gte=start_of_day,
                    requested_at__lt=end_of_day,
                )
                .filter(Q(status=VisitSession.Status.WAITING) | Q(status=VisitSession.Status.ENTERED))
                .order_by("-requested_at")
                .first()
            )

            if active_visit:
                if active_visit.status == VisitSession.Status.ENTERED and not active_visit.re_wait_requested_at:
                    active_visit.re_wait_requested_at = timezone.now()
                    active_visit.save(update_fields=["re_wait_requested_at", "updated_at"])
                return redirect("iomanager_app:customer_home")

            VisitSession.objects.create(customer=customer, status=VisitSession.Status.WAITING)
        return redirect("iomanager_app:customer_home")

    setting = _get_system_setting()
    return render(request, "iomanager_app/customer_home.html", {"greeting_message": setting.greeting_message})


@login_required
def admin_home_view(request):
    return redirect("iomanager_app:admin_status")


def _manager_context(active_menu, active_submenu):
    return {"active_menu": active_menu, "active_submenu": active_submenu}


def _normalized_phone_query(request, key="q"):
    return re.sub(r"\D", "", request.GET.get(key, ""))


def _resolve_page_size(request, default=20):
    try:
        page_size = int(request.GET.get("page_size", str(default)))
    except (TypeError, ValueError):
        return default
    return page_size if page_size in PAGE_SIZE_CHOICES else default


def _paginate_queryset(request, queryset, *, default_page_size=20):
    page_size = _resolve_page_size(request, default=default_page_size)
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(request.GET.get("page"))
    return page_obj, page_obj.object_list, page_size


def _parse_int_field(raw_value, *, default=0, min_value=0):
    try:
        parsed = int(raw_value or default)
    except (TypeError, ValueError):
        return None
    if parsed < min_value:
        return None
    return parsed


def _build_admin_status_context():
    today, start_of_day, end_of_day = _today_bounds()
    active_passes_subquery = CustomerPass.objects.filter(
        customer_id=OuterRef("customer_id"),
        remaining_count__gt=0,
        expires_on__gt=today,
    )
    waiting_visits = (
        VisitSession.objects.select_related("customer")
        .prefetch_related("order_items__product")
        .annotate(has_active_pass=Exists(active_passes_subquery))
        .filter(requested_at__gte=start_of_day, requested_at__lt=end_of_day)
        .filter(
            Q(status=VisitSession.Status.WAITING)
            | Q(status=VisitSession.Status.ENTERED, re_wait_requested_at__isnull=False)
        )
    )
    active_visits = (
        VisitSession.objects.select_related("customer")
        .prefetch_related("order_items__product")
        .annotate(has_active_pass=Exists(active_passes_subquery))
        .filter(requested_at__gte=start_of_day, requested_at__lt=end_of_day)
        .filter(
            Q(status=VisitSession.Status.EXITED)
            | Q(status=VisitSession.Status.ENTERED, re_wait_requested_at__isnull=True)
        )
    )
    product_totals = list(
        VisitOrderItem.objects.filter(
            visit__requested_at__gte=start_of_day,
            visit__requested_at__lt=end_of_day,
        )
        .values("product__name")
        .annotate(total_quantity=Sum("quantity"))
        .order_by("-total_quantity", "product__name")
    )
    return {
        "waiting_visits": waiting_visits,
        "active_visits": active_visits,
        "product_totals": product_totals,
        "product_totals_grand_total": sum(row["total_quantity"] for row in product_totals),
        "now": timezone.localtime(),
    }


@login_required
def admin_status_view(request):
    return render(
        request,
        "iomanager_app/admin_status.html",
        {
            **_manager_context("status", ""),
            **_build_admin_status_context(),
        },
    )


@login_required
def admin_status_panel_view(request):
    return render(request, "iomanager_app/includes/admin_status_panel.html", _build_admin_status_context())


@login_required
def pass_history_view(request):
    _record_expired_pass_transactions(timezone.localdate())
    q = _normalized_phone_query(request)

    rows = PassTransaction.objects.select_related("customer", "template").order_by("-happened_at", "-id")
    if q:
        rows = rows.filter(customer__phone_number__icontains=q)
    page_obj, rows, page_size = _paginate_queryset(request, rows)
    return render(
        request,
        "iomanager_app/pass_history.html",
        {
            **_manager_context("history", "pass_history"),
            "rows": page_obj.object_list,
            "page_obj": page_obj,
            "q": q,
            "page_size": page_size,
        },
    )


@login_required
def visit_history_view(request):
    q = _normalized_phone_query(request)

    rows = (
        VisitSession.objects.select_related("customer")
        .prefetch_related("order_items__product")
        .filter(status__in=[VisitSession.Status.ENTERED, VisitSession.Status.EXITED])
        .order_by("-requested_at", "-id")
    )
    if q:
        rows = rows.filter(customer__phone_number__icontains=q)
    page_obj, rows, page_size = _paginate_queryset(request, rows)
    return render(
        request,
        "iomanager_app/visit_history.html",
        {
            **_manager_context("history", "visit_history"),
            "rows": page_obj.object_list,
            "page_obj": page_obj,
            "q": q,
            "page_size": page_size,
        },
    )


@login_required
def customer_info_view(request):
    q = _normalized_phone_query(request)
    today = timezone.localdate()
    customers = Customer.objects.all()
    if q:
        customers = customers.filter(phone_number__icontains=q)

    active_passes = CustomerPass.objects.filter(customer_id=OuterRef("pk"), remaining_count__gt=0, expires_on__gt=today)
    rows = customers.annotate(has_active_pass=Exists(active_passes)).order_by("-last_visit_at", "-id")
    page_obj, rows, page_size = _paginate_queryset(request, rows)
    return render(
        request,
        "iomanager_app/customer_info.html",
        {
            **_manager_context("customer", "customer_info"),
            "rows": page_obj.object_list,
            "page_obj": page_obj,
            "q": q,
            "page_size": page_size,
        },
    )


@login_required
def customer_profile_view(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    today = timezone.localdate()

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "update_pass_expiry":
            customer_pass = get_object_or_404(
                CustomerPass.objects.select_related("template"),
                id=request.POST.get("customer_pass_id"),
                customer=customer,
            )
            expires_on_raw = request.POST.get("expires_on", "")
            try:
                expires_on = date.fromisoformat(expires_on_raw)
            except ValueError:
                messages.error(request, "만료일 형식이 올바르지 않습니다.")
                return redirect("iomanager_app:customer_profile", customer_id=customer.id)

            customer_pass.expires_on = expires_on
            customer_pass.save(update_fields=["expires_on"])
            messages.success(
                request,
                f"{customer_pass.template.name} 정기권 만료일이 {expires_on.isoformat()}로 변경되었습니다.",
            )
            return redirect("iomanager_app:customer_profile", customer_id=customer.id)

        if action == "delete_customer":
            customer.delete()
            messages.success(request, "고객이 삭제되었습니다.")
            return redirect("iomanager_app:customer_info")

    customer_passes = (
        customer.passes.select_related("template")
        .filter(remaining_count__gt=0, expires_on__gt=today)
        .order_by("expires_on", "id")
    )
    visits = customer.visits.prefetch_related("order_items__product").order_by("-requested_at")
    return render(
        request,
        "iomanager_app/customer_profile.html",
        {
            **_manager_context("customer", "customer_info"),
            "customer": customer,
            "customer_passes": customer_passes,
            "today": today,
            "visits": visits,
        },
    )


@login_required
def pass_customer_view(request):
    q = _normalized_phone_query(request)
    sort = request.GET.get("sort", "asc")
    today = timezone.localdate()
    rows = CustomerPass.objects.select_related("customer", "template").filter(remaining_count__gt=0, expires_on__gt=today)
    if q:
        rows = rows.filter(customer__phone_number__icontains=q)
    if sort == "desc":
        rows = rows.order_by("-expires_on", "-id")
    else:
        sort = "asc"
        rows = rows.order_by("expires_on", "id")
    page_obj, rows, page_size = _paginate_queryset(request, rows)
    return render(
        request,
        "iomanager_app/pass_customer.html",
        {
            **_manager_context("customer", "pass_customer"),
            "rows": page_obj.object_list,
            "page_obj": page_obj,
            "q": q,
            "sort": sort,
            "page_size": page_size,
        },
    )


@login_required
def product_settings_view(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            name = request.POST.get("name", "").strip()
            price = _parse_int_field(request.POST.get("price"), default=0, min_value=0)
            if not name:
                messages.error(request, "상품 이름을 입력해주세요.")
            elif price is None:
                messages.error(request, "가격은 0 이상의 숫자로 입력해주세요.")
            else:
                try:
                    ProductTemplate.objects.create(name=name, price=price)
                    messages.success(request, "상품 템플릿이 생성되었습니다.")
                except IntegrityError:
                    messages.error(request, "이미 존재하는 상품 이름입니다.")
        elif action == "delete":
            ProductTemplate.objects.filter(id=request.POST.get("template_id")).delete()
            messages.success(request, "상품 템플릿이 삭제되었습니다.")
        return redirect("iomanager_app:product_settings")

    templates = ProductTemplate.objects.all()
    return render(
        request,
        "iomanager_app/product_settings.html",
        {**_manager_context("settings", "product_settings"), "templates": templates},
    )


@login_required
def pass_settings_view(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            name = request.POST.get("name", "").strip()
            issue_count = _parse_int_field(request.POST.get("issue_count"), default=1, min_value=1)
            valid_days = _parse_int_field(request.POST.get("valid_days"), default=30, min_value=1)
            if not name:
                messages.error(request, "정기권 이름을 입력해주세요.")
            elif issue_count is None or valid_days is None:
                messages.error(request, "발행 개수와 유효기간은 1 이상의 숫자로 입력해주세요.")
            else:
                try:
                    PassTemplate.objects.create(name=name, issue_count=issue_count, valid_days=valid_days)
                    messages.success(request, "정기권 템플릿이 생성되었습니다.")
                except IntegrityError:
                    messages.error(request, "이미 존재하는 정기권 이름입니다.")
        elif action == "delete":
            deleted, _ = PassTemplate.objects.filter(id=request.POST.get("template_id")).delete()
            if deleted:
                messages.success(request, "정기권 템플릿이 삭제되었습니다.")
            else:
                messages.info(request, "이미 삭제되었거나 존재하지 않는 정기권 템플릿입니다.")
        return redirect("iomanager_app:pass_settings")

    templates = PassTemplate.objects.all()
    return render(
        request,
        "iomanager_app/pass_settings.html",
        {**_manager_context("settings", "pass_settings"), "templates": templates},
    )


@login_required
def system_settings_view(request):
    setting = _get_system_setting()
    if request.method == "POST":
        setting.greeting_message = request.POST.get("greeting_message", "").strip()
        setting.save(update_fields=["greeting_message", "updated_at"])
        messages.success(request, "시스템 설정이 저장되었습니다.")
        return redirect("iomanager_app:system_settings")

    return render(
        request,
        "iomanager_app/system_settings.html",
        {
            **_manager_context("settings", "system_settings"),
            "setting": setting,
        },
    )


@login_required
def customer_detail_view(request, visit_id):
    visit = get_object_or_404(VisitSession.objects.select_related("customer"), id=visit_id)
    today = timezone.localdate()
    products = ProductTemplate.objects.all()
    customer_passes = visit.customer.passes.select_related("template").filter(remaining_count__gt=0, expires_on__gt=today)
    existing = {item.product_id: item for item in visit.order_items.all()}

    if request.method == "POST":
        action = request.POST.get("action")
        for product in products:
            qty = int(request.POST.get(f"product_{product.id}", "0") or 0)
            item = existing.get(product.id)
            if qty <= 0:
                if item:
                    item.delete()
                continue
            if item:
                item.quantity = qty
                item.save(update_fields=["quantity"])
            else:
                VisitOrderItem.objects.create(
                    visit=visit,
                    product=product,
                    product_name_snapshot=product.name,
                    quantity=qty,
                )

        now = timezone.now()

        def _set_entered(current_visit):
            current_visit.status = VisitSession.Status.ENTERED
            if not current_visit.entered_at:
                current_visit.entered_at = now
            current_visit.re_wait_requested_at = None
            current_visit.customer.last_visit_at = now
            current_visit.customer.visit_count += 1
            current_visit.customer.save(update_fields=["last_visit_at", "visit_count"])
            current_visit.save(update_fields=["status", "entered_at", "re_wait_requested_at", "updated_at"])

        if action == "enter" and visit.status == VisitSession.Status.WAITING:
            _set_entered(visit)
        elif action == "confirm" and visit.status == VisitSession.Status.WAITING:
            _set_entered(visit)
        elif action == "confirm" and visit.status == VisitSession.Status.ENTERED and visit.re_wait_requested_at:
            visit.re_wait_requested_at = None
            visit.save(update_fields=["re_wait_requested_at", "updated_at"])
        elif action == "exit" and visit.status == VisitSession.Status.ENTERED:
            visit.re_wait_requested_at = None
            visit.status = VisitSession.Status.EXITED
            visit.exited_at = now
            visit.save(update_fields=["status", "exited_at", "re_wait_requested_at", "updated_at"])
        elif action == "cancel_waiting" and visit.status == VisitSession.Status.WAITING:
            visit.delete()
        return redirect("iomanager_app:admin_status")

    product_rows = [{"product": product, "quantity": existing.get(product.id).quantity if existing.get(product.id) else 0} for product in products]
    return render(
        request,
        "iomanager_app/customer_detail.html",
        {"visit": visit, "product_rows": product_rows, "customer_passes": customer_passes},
    )


@login_required
def pass_issue_view(request, visit_id):
    visit = get_object_or_404(VisitSession.objects.select_related("customer"), id=visit_id)
    templates = PassTemplate.objects.all()
    if request.method == "POST":
        if request.POST.get("action") == "issue":
            if not templates.exists():
                messages.error(request, "발행 가능한 정기권 템플릿이 없습니다.")
                return redirect("iomanager_app:pass_issue", visit_id=visit.id)

            template = get_object_or_404(PassTemplate, id=request.POST.get("template_id"))
            try:
                issue_count = int(request.POST.get("issue_count", str(template.issue_count)) or template.issue_count)
            except (TypeError, ValueError):
                messages.error(request, "발행 개수는 숫자로 입력해주세요.")
                return redirect("iomanager_app:pass_issue", visit_id=visit.id)

            if issue_count <= 0:
                messages.error(request, "발행 개수는 1 이상이어야 합니다.")
                return redirect("iomanager_app:pass_issue", visit_id=visit.id)

            expires_on_raw = request.POST.get("expires_on", "")
            if expires_on_raw:
                try:
                    expires_on = date.fromisoformat(expires_on_raw)
                except ValueError:
                    messages.error(request, "만료일 형식이 올바르지 않습니다.")
                    return redirect("iomanager_app:pass_issue", visit_id=visit.id)
            else:
                expires_on = timezone.localdate() + timedelta(days=template.valid_days)

            customer_pass = CustomerPass.objects.create(
                customer=visit.customer,
                template=template,
                remaining_count=issue_count,
                expires_on=expires_on,
            )
            PassTransaction.objects.create(
                customer=visit.customer,
                template=template,
                template_name_snapshot=template.name,
                quantity=issue_count,
                status=PassTransaction.Status.ISSUED,
                customer_pass=customer_pass,
                visit=visit,
            )
        return redirect("iomanager_app:customer_detail", visit_id=visit.id)
    return render(request, "iomanager_app/pass_issue.html", {"visit": visit, "templates": templates})


@login_required
def pass_use_view(request, visit_id):
    visit = get_object_or_404(VisitSession.objects.select_related("customer"), id=visit_id)
    today = timezone.localdate()
    customer_passes = visit.customer.passes.select_related("template").filter(remaining_count__gt=0, expires_on__gt=today)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "use":
            requested_counts = []
            for customer_pass in customer_passes:
                raw_count = request.POST.get(f"use_count_{customer_pass.id}", "0")
                try:
                    use_count = int(raw_count or 0)
                except (TypeError, ValueError):
                    use_count = 0
                if use_count > 0:
                    requested_counts.append((customer_pass.id, use_count))

            if not requested_counts:
                messages.info(request, "사용할 정기권 수량을 선택해주세요.")
                return redirect("iomanager_app:pass_use", visit_id=visit.id)

            with transaction.atomic():
                pass_ids = [pass_id for pass_id, _ in requested_counts]
                locked_passes = {
                    row.id: row
                    for row in CustomerPass.objects.select_for_update()
                    .select_related("template")
                    .filter(id__in=pass_ids, customer=visit.customer, expires_on__gt=today)
                }

                for pass_id, use_count in requested_counts:
                    customer_pass = locked_passes.get(pass_id)
                    if not customer_pass or customer_pass.remaining_count < use_count:
                        messages.error(request, "정기권 잔여 수량이 부족합니다. 다시 확인해주세요.")
                        return redirect("iomanager_app:pass_use", visit_id=visit.id)

                for pass_id, use_count in requested_counts:
                    customer_pass = locked_passes[pass_id]
                    customer_pass.remaining_count -= use_count
                    customer_pass.save(update_fields=["remaining_count"])
                    PassTransaction.objects.create(
                        customer=visit.customer,
                        template=customer_pass.template,
                        template_name_snapshot=customer_pass.template.name,
                        quantity=use_count,
                        status=PassTransaction.Status.USED,
                        customer_pass=customer_pass,
                        visit=visit,
                    )

            messages.success(request, "정기권 사용이 적용되었습니다.")
        return redirect("iomanager_app:customer_detail", visit_id=visit.id)
    return render(request, "iomanager_app/pass_use.html", {"visit": visit, "customer_passes": customer_passes})
