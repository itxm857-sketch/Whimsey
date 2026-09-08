from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from ..models import Product

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')


def get_cart():
    return session.setdefault('cart', {})


def clean_cart():
    cart = get_cart()
    valid = {}
    for pid, qty in cart.items():
        try:
            product = Product.query.filter_by(id=int(pid), active=True).first()
            qty = int(qty)
            if product and qty > 0:
                valid[str(product.id)] = min(qty, product.stock)
        except (ValueError, TypeError):
            continue
    valid = {k: v for k, v in valid.items() if v > 0}
    session['cart'] = valid
    session.modified = True
    return valid


@cart_bp.route('')
def view_cart():
    cart = clean_cart()
    items = []
    subtotal = 0
    for pid, qty in cart.items():
        product = Product.query.get(int(pid))
        if not product: continue
        line = product.current_price * qty
        subtotal += line
        items.append({'product': product, 'quantity': qty, 'line_total': line})
    shipping = 300 if items else 0
    return render_template('cart.html', items=items, subtotal=subtotal, shipping=shipping, total=subtotal + shipping)


@cart_bp.route('/add/<int:product_id>', methods=['POST'])
def add(product_id):
    product = Product.query.filter_by(id=product_id, active=True).first_or_404()
    qty = request.form.get('quantity', 1, type=int)
    if qty < 1: qty = 1
    if product.stock <= 0:
        flash('This product is out of stock.', 'error')
        return redirect(request.referrer or url_for('shop.shop'))
    cart = get_cart()
    existing = int(cart.get(str(product.id), 0))
    if existing + qty > product.stock:
        flash(f'Only {product.stock} unit(s) are available.', 'error')
    else:
        cart[str(product.id)] = existing + qty
        session.modified = True
        flash(f'{product.name} was added to your cart.', 'success')
    if request.form.get('buy_now') == '1':
        if __import__('flask_login').current_user.is_authenticated:
            return redirect(url_for('orders.checkout'))
        return redirect(url_for('auth.login', next=url_for('orders.checkout')))
    return redirect(request.referrer or url_for('cart.view_cart'))


@cart_bp.route('/update/<int:product_id>', methods=['POST'])
def update(product_id):
    product = Product.query.filter_by(id=product_id, active=True).first_or_404()
    qty = request.form.get('quantity', type=int)
    cart = get_cart()
    if qty is None or qty < 1:
        cart.pop(str(product.id), None)
        flash('Item removed from your cart.', 'success')
    elif qty > product.stock:
        cart[str(product.id)] = max(product.stock, 0)
        flash(f'Only {product.stock} unit(s) are available.', 'error')
    else:
        cart[str(product.id)] = qty
    session.modified = True
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/remove/<int:product_id>', methods=['POST'])
def remove(product_id):
    cart = get_cart()
    cart.pop(str(product_id), None)
    session.modified = True
    flash('Item removed from your cart.', 'success')
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/clear', methods=['POST'])
def clear():
    session['cart'] = {}
    flash('Your cart has been cleared.', 'success')
    return redirect(url_for('cart.view_cart'))
