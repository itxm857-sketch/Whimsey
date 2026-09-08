from decimal import Decimal
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models import Order, OrderItem, Product
from ..utils.helpers import unique_order_number

orders_bp = Blueprint('orders', __name__)


def cart_items_for_checkout():
    cart = session.get('cart', {})
    result = []
    for pid, qty in cart.items():
        try:
            product = Product.query.filter_by(id=int(pid), active=True).first()
            qty = int(qty)
        except (ValueError, TypeError):
            product, qty = None, 0
        if product and qty > 0:
            result.append((product, qty))
    return result


@orders_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    items = cart_items_for_checkout()
    if not items:
        flash('Your cart is empty.', 'error')
        return redirect(url_for('cart.view_cart'))
    subtotal = sum((p.current_price * q for p, q in items), Decimal('0.00'))
    shipping = Decimal(str(__import__('flask').current_app.config['SHIPPING_FEE']))
    total = subtotal + shipping
    if request.method == 'POST':
        name = request.form.get('customer_name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip().lower()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        postal = request.form.get('postal_code', '').strip()
        notes = request.form.get('notes', '').strip()
        errors = []
        if not name: errors.append('Full name is required.')
        if not phone: errors.append('Phone number is required.')
        if not email or '@' not in email: errors.append('Enter a valid email address.')
        if not address: errors.append('Delivery address is required.')
        if not city: errors.append('City is required.')
        if errors:
            for e in errors: flash(e, 'error')
            return render_template('checkout.html', items=items, subtotal=subtotal, shipping=shipping, total=total)

        try:
            # Re-read and lock every product row before calculating anything.
            locked = []
            for product, qty in items:
                stmt = db.select(Product).where(Product.id == product.id, Product.active.is_(True)).with_for_update()
                fresh = db.session.execute(stmt).scalar_one_or_none()
                if not fresh or qty > fresh.stock:
                    raise ValueError(f'Not enough stock for {product.name}. Please review your cart.')
                locked.append((fresh, qty))
            subtotal = sum((p.current_price * q for p, q in locked), Decimal('0.00'))
            total = subtotal + shipping
            order = Order(order_number=unique_order_number(), user_id=current_user.id, customer_name=name,
                          email=email, phone=phone, address=address, city=city, postal_code=postal or None,
                          subtotal=subtotal, shipping_fee=shipping, total=total, notes=notes or None,
                          status='Pending', stock_deducted=False)
            db.session.add(order)
            db.session.flush()
            for product, qty in locked:
                line = product.current_price * qty
                db.session.add(OrderItem(order_id=order.id, product_id=product.id,
                                         product_name_snapshot=product.name, price_snapshot=product.current_price,
                                         quantity=qty, subtotal=line))
                product.stock -= qty
            order.stock_deducted = True
            db.session.commit()
            session['cart'] = {}
            flash(f'Order {order.order_number} placed successfully!', 'success')
            return redirect(url_for('orders.detail', order_number=order.order_number))
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), 'error')
            return redirect(url_for('cart.view_cart'))
        except Exception:
            db.session.rollback()
            flash('We could not place your order. Please try again.', 'error')
            return render_template('checkout.html', items=items, subtotal=subtotal, shipping=shipping, total=total)
    return render_template('checkout.html', items=items, subtotal=subtotal, shipping=shipping, total=total)


@orders_bp.route('/orders')
@login_required
def list_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=orders)


@orders_bp.route('/orders/<order_number>')
@login_required
def detail(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    if order.user_id != current_user.id and current_user.role != 'admin':
        from flask import abort
        abort(403)
    return render_template('order_detail.html', order=order)
