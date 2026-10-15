import os
import stripe
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Product, Category, HomepageImage, Order, OrderItem

def get_base_url(request):
    """Get the base URL for the current environment"""
    if request.is_secure():
        return f'https://{request.get_host()}'
    return f'http://{request.get_host()}'


stripe.api_key = settings.STRIPE_SECRET_KEY


# ── CART HELPERS ──

def get_cart(request):
    """Get cart from session. Format: {product_id: quantity}"""
    cart = request.session.get('cart', {})
    return cart


def cart_count(request):
    """Total number of items in cart"""
    cart = get_cart(request)
    return sum(cart.values())


def cart_total(cart):
    """Total price of all items in cart (in sen)"""
    total = 0
    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        total += product.price * quantity
    return total


# ── STOREFRONT VIEWS ──

def product_list(request):
    """Show all products on the storefront"""
    products = Product.objects.all()
    categories = Category.objects.all()
    homepage_images = HomepageImage.objects.filter(is_active=True)
    return render(request, 'store/product_list.html', {
        'products': products,
        'categories': categories,
        'homepage_images': homepage_images,
        'cart_count': cart_count(request),
    })


def product_list_by_category(request, category_id):
    """Show products filtered by category"""
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    categories = Category.objects.all()
    return render(request, 'store/product_list.html', {
        'products': products,
        'categories': categories,
        'current_category': category,
        'homepage_images': HomepageImage.objects.none(),  # empty = show category banner
        'cart_count': cart_count(request),
    })


def product_detail(request, product_id):
    """Show single product details with add to cart button"""
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'store/product_detail.html', {
        'product': product,
        'cart_count': cart_count(request),
    })


# ── CART VIEWS ──

def add_to_cart(request, product_id):
    """Add a product to the cart (or increase quantity)"""
    cart = get_cart(request)
    pid = str(product_id)
    cart[pid] = cart.get(pid, 0) + 1
    request.session['cart'] = cart
    return redirect('store:cart_view')


def remove_from_cart(request, product_id):
    """Remove a product from the cart entirely"""
    cart = get_cart(request)
    pid = str(product_id)
    if pid in cart:
        del cart[pid]
    request.session['cart'] = cart
    return redirect('store:cart_view')


def update_cart(request, product_id):
    """Update quantity for a product in cart"""
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart = get_cart(request)
        pid = str(product_id)
        if pid in cart:
            if quantity > 0:
                cart[pid] = quantity
            else:
                del cart[pid]
        request.session['cart'] = cart
    return redirect('store:cart_view')


def cart_view(request):
    """Show cart contents with total"""
    cart = get_cart(request)
    items = []
    total = 0
    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        line_total = product.price * quantity
        total += line_total
        items.append({
            'product': product,
            'quantity': quantity,
            'line_total': line_total,
            'line_total_display': f"RM {line_total / 100:.2f}",
        })
    return render(request, 'store/cart.html', {
        'items': items,
        'total': total,
        'total_display': f"RM {total / 100:.2f}",
        'cart_count': cart_count(request),
    })


# ── CHECKOUT VIEWS ──

def generate_order_id():
    """Generate a human-readable order ID like ORD-001"""
    last_order = Order.objects.order_by('-id').first()
    if last_order and last_order.order_id:
        # Extract number from last order_id
        num = int(last_order.order_id.split('-')[1])
        return f"ORD-{num + 1:03d}"
    return "ORD-001"


def checkout_form(request):
    """Show form for email, name, phone, address"""
    cart = get_cart(request)
    if not cart:
        return redirect('store:product_list')

    total = cart_total(cart)
    return render(request, 'store/checkout.html', {
        'total': total,
        'total_display': f"RM {total / 100:.2f}",
        'cart_count': cart_count(request),
    })


def process_checkout(request):
    """Create order + order items, create Stripe session, redirect to Stripe"""
    if request.method != 'POST':
        return redirect('store:checkout_form')

    cart = get_cart(request)
    if not cart:
        return redirect('store:product_list')

    # Step 1: Create Order with shipping details
    order = Order.objects.create(
        order_id=generate_order_id(),
        email=request.POST.get('email'),
        name=request.POST.get('name'),
        phone=request.POST.get('phone'),
        address=request.POST.get('address'),
    )

    # Step 2: Create OrderItems (snapshot of cart)
    line_items = []
    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price_at_purchase=product.price,
        )
        line_items.append({
            'price_data': {
                'currency': 'myr',
                'product_data': {'name': product.name},
                'unit_amount': product.price,
            },
            'quantity': quantity,
        })

    # Step 3: Create Stripe Checkout Session with ALL items
    base_url = get_base_url(request)
    session = stripe.checkout.Session.create(
        line_items=line_items,
        mode='payment',
        success_url=f'{base_url}/success/{order.id}/',
        cancel_url=f'{base_url}/cart/',
    )

    # Step 4: Save session ID to order
    order.stripe_session_id = session.id
    order.save()

    # Step 5: Clear the cart
    request.session['cart'] = {}

    # Step 6: Redirect to Stripe
    return redirect(session.url, code=303)


def success_page(request, order_id):
    """Show order confirmation with order_id and shipping details"""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'store/success.html', {
        'order': order,
        'cart_count': 0,
    })


# ── TRACK ORDER ──

def track_order(request):
    """Show form to enter order ID"""
    return render(request, 'store/track_order.html', {
        'cart_count': cart_count(request),
    })


def track_result(request):
    """Look up order by order_id and show tracking details"""
    query = request.GET.get('order_id', '').strip().upper()
    if not query:
        return redirect('store:track_order')

    try:
        order = Order.objects.get(order_id=query)
    except Order.DoesNotExist:
        return render(request, 'store/track_order.html', {
            'cart_count': cart_count(request),
            'error': f'Order "{query}" not found. Check your order ID and try again.',
        })

    return render(request, 'store/track_result.html', {
        'order': order,
        'cart_count': cart_count(request),
    })


def order_pdf(request, order_id):
    """Generate PDF invoice/receipt for an order"""
    from django.template.loader import render_to_string
    from weasyprint import HTML
    from django.http import HttpResponse

    try:
        order = Order.objects.get(order_id=order_id.upper())
    except Order.DoesNotExist:
        return redirect('store:track_order')

    # Render HTML template to string
    html_string = render_to_string('store/order_pdf.html', {'order': order})

    # Generate PDF
    pdf = HTML(string=html_string).write_pdf()

    # Return as downloadable PDF
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{order.order_id}.pdf"'
    return response


# ── EMAIL ──

def send_receipt_email(order):
    """Send order receipt email to customer after payment"""
    from django.core.mail import EmailMessage
    from django.template.loader import render_to_string
    from django.conf import settings as dj_settings

    base_url = 'https://' + dj_settings.ALLOWED_HOSTS[0] if dj_settings.ALLOWED_HOSTS else 'http://localhost:8090'

    # Render HTML email from template
    html_content = render_to_string('store/email_receipt.html', {'order': order})

    # Build plain text fallback
    items_text = ""
    for item in order.items.all():
        items_text += f"  {item.quantity}x {item.product.name} - {item.line_total_display}\n"

    text_content = f"""
Thank you for your order!

Order ID: {order.order_id}
Status: PAID

Items:
{items_text}
Total: {order.total_display}

Shipping to:
{order.name}
{order.address}

Track your order at: {base_url}/track/

Your Shop
    """.strip()

    email = EmailMessage(
        subject=f'Order Receipt - {order.order_id}',
        body=text_content,
        from_email='shop@yourshop.com',
        to=[order.email],
    )
    email.content_subtype = 'html'
    email.body = html_content
    email.send()


# ── WEBHOOK ──

@csrf_exempt
def webhook(request):
    """Stripe webhook — the source of truth for payment status"""
    import logging
    logger = logging.getLogger(__name__)

    if request.method == 'POST':
        payload = request.body
        sig_header = request.headers.get('Stripe-Signature', '')
        endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

        logger.info(f"Webhook received. Secret exists: {bool(endpoint_secret)}. Sig exists: {bool(sig_header)}")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError as e:
            logger.error(f"Webhook ValueError: {e}")
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook SignatureVerificationError: {e}")
            return HttpResponse(status=400)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            try:
                order = Order.objects.get(stripe_session_id=session.id)
                order.paid = True
                order.save()

                # Send receipt email
                send_receipt_email(order)

            except Order.DoesNotExist:
                pass

    return HttpResponse(status=200)
