from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("<int:pk>/invoice/", views.order_invoice_pdf, name="invoice_pdf"),
]
