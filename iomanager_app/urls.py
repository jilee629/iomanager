from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import (
    IomanagerLoginView,
    admin_home_view,
    admin_status_view,
    customer_detail_view,
    customer_info_view,
    customer_profile_view,
    customer_home_view,
    pass_customer_view,
    pass_history_view,
    pass_issue_view,
    pass_settings_view,
    pass_use_view,
    product_settings_view,
    root_redirect,
    selection_view,
    system_settings_view,
    visit_history_view,
)

app_name = "iomanager_app"

urlpatterns = [
    path("", root_redirect, name="root"),
    path("login/", IomanagerLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="iomanager_app:login"), name="logout"),
    path("selection/", selection_view, name="selection"),
    path("customer/", customer_home_view, name="customer_home"),
    path("manager/", admin_home_view, name="admin_home"),
    path("manager/status/", admin_status_view, name="admin_status"),
    path("manager/history/pass/", pass_history_view, name="pass_history"),
    path("manager/history/visit/", visit_history_view, name="visit_history"),
    path("manager/customer/info/", customer_info_view, name="customer_info"),
    path("manager/customer/info/<int:customer_id>/", customer_profile_view, name="customer_profile"),
    path("manager/customer/pass/", pass_customer_view, name="pass_customer"),
    path("manager/settings/product/", product_settings_view, name="product_settings"),
    path("manager/settings/pass/", pass_settings_view, name="pass_settings"),
    path("manager/settings/system/", system_settings_view, name="system_settings"),
    path("manager/customer-detail/<int:visit_id>/", customer_detail_view, name="customer_detail"),
    path("manager/pass-issue/<int:visit_id>/", pass_issue_view, name="pass_issue"),
    path("manager/pass-use/<int:visit_id>/", pass_use_view, name="pass_use"),
]
