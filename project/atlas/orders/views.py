import io

from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from .models import Order


@login_required
@permission_required("orders.view_order", raise_exception=True)
def order_invoice_pdf(request, pk):
    """Generates the invoice on demand rather than storing a file per
    order — cheap to build, and it can never go stale (edit an OrderItem,
    the next download reflects it) the way a pre-rendered file would."""
    order = get_object_or_404(
        Order.objects.select_related("customer").prefetch_related("items__product"), pk=pk
    )

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(1 * inch, height - 1 * inch, f"Atlas — Invoice for Order #{order.pk}")

    pdf.setFont("Helvetica", 11)
    y = height - 1.5 * inch
    pdf.drawString(1 * inch, y, f"Customer: {order.customer.full_name} ({order.customer.email})")
    y -= 0.25 * inch
    pdf.drawString(1 * inch, y, f"Status: {order.get_status_display()}")
    y -= 0.25 * inch
    pdf.drawString(1 * inch, y, f"Placed: {order.created_at:%Y-%m-%d %H:%M}")

    y -= 0.5 * inch
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(1 * inch, y, "Product")
    pdf.drawString(4 * inch, y, "Qty")
    pdf.drawString(4.75 * inch, y, "Unit price")
    pdf.drawString(6 * inch, y, "Line total")

    pdf.setFont("Helvetica", 11)
    for item in order.items.all():
        y -= 0.25 * inch
        pdf.drawString(1 * inch, y, item.product.name)
        pdf.drawString(4 * inch, y, str(item.quantity))
        pdf.drawString(4.75 * inch, y, f"${item.unit_price:.2f}")
        pdf.drawString(6 * inch, y, f"${item.line_total:.2f}")

    y -= 0.5 * inch
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(1 * inch, y, f"Total: ${order.total:.2f}")

    pdf.showPage()
    pdf.save()

    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="order-{order.pk}-invoice.pdf"'
    return response
