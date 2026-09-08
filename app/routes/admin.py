from decimal import Decimal
from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import desc, func, or_
from flask_login import current_user
from ..extensions import db
from ..models import Category, Message, Order, OrderItem, Product, User
from ..utils.helpers import admin_required, parse_money, unique_slug
from ..utils.storage import upload_product_image

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
STATUSES = ['Pending', 'Confirmed', 'Processing', 'Shipped', 'Delivered', 'Cancelled']


@admin_bp.route('')
@admin_required
def dashboard():
    total_sales = db.session.query(func.coalesce(func.sum(Order.total), 0)).filter(Order.status != 'Cancelled').scalar()
    stats = {
        'sales': total_sales,
        'orders': Order.query.count(),
        'pending': Order.query.filter_by(status='Pending').count(),
        'completed': Order.query.filter_by(status='Delivered').count(),
        'customers': User.query.filter_by(role='customer').count(),
        'products': Product.query.count(),
        'low_stock': Product.query.filter(Product.stock > 0, Product.stock <= Product.low_stock_threshold).count(),
        'out_stock': Product.query.filter(Product.stock <= 0).count(),
    }
    recent_orders = Order.query.order_by(desc(Order.created_at)).limit(8).all()
    recent_messages = Message.query.order_by(desc(Message.created_at)).limit(6).all()
    return render_template('admin/dashboard.html', stats=stats, recent_orders=recent_orders, recent_messages=recent_messages)


@admin_bp.route('/products')
@admin_required
def products():
    q = request.args.get('q', '').strip()
    query = Product.query.order_by(desc(Product.created_at))
    if q:
        term = f'%{q}%'
        query = query.filter(or_(Product.name.ilike(term), Product.sku.ilike(term)))
    page = query.paginate(page=request.args.get('page', 1, type=int), per_page=20, error_out=False)
    return render_template('admin/products.html', products=page.items, pagination=page, q=q)


def product_form(product=None):
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/product_form.html', product=product, categories=categories)


@admin_bp.route('/products/new', methods=['GET', 'POST'])
@admin_required
def add_product():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            sku = request.form.get('sku', '').strip().upper()
            price = parse_money(request.form.get('price'))
            sale_raw = request.form.get('sale_price', '').strip()
            sale = parse_money(sale_raw) if sale_raw else None
            stock = int(request.form.get('stock', 0))
            threshold = int(request.form.get('low_stock_threshold', 5))
            category_id = request.form.get('category_id', type=int)
            if not name or not sku: raise ValueError('Name and SKU are required.')
            if stock < 0 or threshold < 0: raise ValueError('Stock values cannot be negative.')
            if sale is not None and sale >= price: raise ValueError('Sale price must be lower than the regular price.')
            if Product.query.filter_by(sku=sku).first(): raise ValueError('SKU already exists.')
            image_url = request.form.get('image_url', '').strip() or None
            additional_images = [x.strip() for x in request.form.get('additional_images', '').splitlines() if x.strip()]
            upload = request.files.get('image')
            if upload and upload.filename:
                image_url = upload_product_image(upload)
            product = Product(name=name, slug=unique_slug(Product, name), description=request.form.get('description','').strip(),
                              price=price, sale_price=sale, stock=stock, low_stock_threshold=threshold, sku=sku,
                              category_id=category_id or None, image_url=image_url, additional_images=additional_images,
                              featured='featured' in request.form, active='active' in request.form)
            db.session.add(product)
            db.session.commit()
            flash('Product created successfully.', 'success')
            return redirect(url_for('admin.products'))
        except Exception as exc:
            db.session.rollback()
            flash(str(exc), 'error')
    return product_form()


@admin_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            sku = request.form.get('sku', '').strip().upper()
            price = parse_money(request.form.get('price'))
            sale_raw = request.form.get('sale_price', '').strip()
            sale = parse_money(sale_raw) if sale_raw else None
            stock = int(request.form.get('stock', 0))
            threshold = int(request.form.get('low_stock_threshold', 5))
            if not name or not sku: raise ValueError('Name and SKU are required.')
            if stock < 0 or threshold < 0: raise ValueError('Stock values cannot be negative.')
            if sale is not None and sale >= price: raise ValueError('Sale price must be lower than the regular price.')
            duplicate = Product.query.filter(Product.sku == sku, Product.id != product.id).first()
            if duplicate: raise ValueError('SKU already exists.')
            product.name = name
            product.slug = unique_slug(Product, name, product.id)
            product.description = request.form.get('description','').strip()
            product.price = price
            product.sale_price = sale
            product.stock = stock
            product.low_stock_threshold = threshold
            product.sku = sku
            product.category_id = request.form.get('category_id', type=int) or None
            product.additional_images = [x.strip() for x in request.form.get('additional_images', '').splitlines() if x.strip()]
            product.featured = 'featured' in request.form
            product.active = 'active' in request.form
            image_url = request.form.get('image_url', '').strip()
            upload = request.files.get('image')
            if upload and upload.filename:
                image_url = upload_product_image(upload)
            if image_url: product.image_url = image_url
            db.session.commit()
            flash('Product updated successfully.', 'success')
            return redirect(url_for('admin.products'))
        except Exception as exc:
            db.session.rollback()
            flash(str(exc), 'error')
    return product_form(product)


@admin_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    if OrderItem.query.filter_by(product_id=product.id).first():
        flash('This product is part of historical orders. Deactivate it instead of deleting it.', 'error')
        return redirect(url_for('admin.products'))
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted.', 'success')
    return redirect(url_for('admin.products'))


@admin_bp.route('/categories', methods=['GET', 'POST'])
@admin_required
def categories():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Category name is required.', 'error')
        elif Category.query.filter(func.lower(Category.name) == name.lower()).first():
            flash('Category already exists.', 'error')
        else:
            db.session.add(Category(name=name, slug=unique_slug(Category, name), description=request.form.get('description','').strip()))
            db.session.commit()
            flash('Category created.', 'success')
    return render_template('admin/categories.html', categories=Category.query.order_by(Category.name).all())


@admin_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@admin_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    category.products.update({'category_id': None})
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted.', 'success')
    return redirect(url_for('admin.categories'))


@admin_bp.route('/orders')
@admin_required
def orders():
    q = request.args.get('q', '').strip()
    status = request.args.get('status', '').strip()
    query = Order.query.order_by(desc(Order.created_at))
    if q:
        term = f'%{q}%'
        query = query.filter(or_(Order.order_number.ilike(term), Order.customer_name.ilike(term), Order.email.ilike(term)))
    if status in STATUSES: query = query.filter_by(status=status)
    page = query.paginate(page=request.args.get('page', 1, type=int), per_page=20, error_out=False)
    return render_template('admin/orders.html', orders=page.items, pagination=page, statuses=STATUSES, q=q, status=status)


@admin_bp.route('/orders/<int:order_id>')
@admin_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order, statuses=STATUSES)


@admin_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    if new_status not in STATUSES:
        flash('Invalid order status.', 'error')
        return redirect(url_for('admin.order_detail', order_id=order.id))
    try:
        if new_status == 'Cancelled' and order.status != 'Cancelled' and order.stock_deducted:
            for item in order.items:
                if item.product_id:
                    product = db.session.execute(db.select(Product).where(Product.id == item.product_id).with_for_update()).scalar_one_or_none()
                    if product: product.stock += item.quantity
            order.stock_deducted = False
        elif order.status == 'Cancelled' and new_status != 'Cancelled':
            # Re-activate only if enough stock is available, restoring the same stock reservation.
            for item in order.items:
                if item.product_id:
                    product = db.session.execute(db.select(Product).where(Product.id == item.product_id).with_for_update()).scalar_one_or_none()
                    if not product or product.stock < item.quantity:
                        raise ValueError(f'Not enough stock to reactivate {item.product_name_snapshot}.')
            for item in order.items:
                if item.product_id:
                    product = db.session.get(Product, item.product_id)
                    product.stock -= item.quantity
            order.stock_deducted = True
        order.status = new_status
        db.session.commit()
        flash('Order status updated.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(str(exc), 'error')
    return redirect(url_for('admin.order_detail', order_id=order.id))


@admin_bp.route('/orders/<int:order_id>/delete', methods=['POST'])
@admin_required
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    try:
        if order.stock_deducted:
            for item in order.items:
                if item.product_id:
                    product = db.session.execute(db.select(Product).where(Product.id == item.product_id).with_for_update()).scalar_one_or_none()
                    if product: product.stock += item.quantity
            order.stock_deducted = False
        db.session.delete(order)
        db.session.commit()
        flash('Order deleted and any deducted stock was restored exactly once.', 'success')
    except Exception as exc:
        db.session.rollback()
        flash(str(exc), 'error')
    return redirect(url_for('admin.orders'))


@admin_bp.route('/customers')
@admin_required
def customers():
    q = request.args.get('q', '').strip()
    query = User.query.filter_by(role='customer').order_by(desc(User.created_at))
    if q:
        term = f'%{q}%'
        query = query.filter(or_(User.name.ilike(term), User.email.ilike(term), User.phone.ilike(term)))
    page = query.paginate(page=request.args.get('page', 1, type=int), per_page=20, error_out=False)
    return render_template('admin/customers.html', customers=page.items, pagination=page, q=q)


@admin_bp.route('/customers/<int:user_id>')
@admin_required
def customer_detail(user_id):
    customer = User.query.filter_by(id=user_id, role='customer').first_or_404()
    orders = Order.query.filter_by(user_id=customer.id).order_by(desc(Order.created_at)).all()
    spending = sum((o.total for o in orders if o.status != 'Cancelled'), Decimal('0.00'))
    return render_template('admin/customer_detail.html', customer=customer, orders=orders, spending=spending)


@admin_bp.route('/customers/<int:user_id>/toggle', methods=['POST'])
@admin_required
def toggle_customer(user_id):
    customer = User.query.filter_by(id=user_id, role='customer').first_or_404()
    customer.is_active = not customer.is_active
    db.session.commit()
    flash('Customer account status updated.', 'success')
    return redirect(url_for('admin.customer_detail', user_id=customer.id))


@admin_bp.route('/messages')
@admin_required
def messages():
    q = request.args.get('q', '').strip()
    query = Message.query.order_by(desc(Message.created_at))
    if q:
        term = f'%{q}%'
        query = query.filter(or_(Message.name.ilike(term), Message.email.ilike(term), Message.subject.ilike(term), Message.message.ilike(term)))
    page = query.paginate(page=request.args.get('page', 1, type=int), per_page=20, error_out=False)
    return render_template('admin/messages.html', messages=page.items, pagination=page, q=q)


@admin_bp.route('/messages/<int:message_id>')
@admin_required
def message_detail(message_id):
    message = Message.query.get_or_404(message_id)
    message.is_read = True
    db.session.commit()
    return render_template('admin/message_detail.html', message=message)


@admin_bp.route('/messages/<int:message_id>/toggle', methods=['POST'])
@admin_required
def toggle_message(message_id):
    message = Message.query.get_or_404(message_id)
    message.is_read = not message.is_read
    db.session.commit()
    return redirect(url_for('admin.messages'))


@admin_bp.route('/messages/<int:message_id>/delete', methods=['POST'])
@admin_required
def delete_message(message_id):
    message = Message.query.get_or_404(message_id)
    db.session.delete(message)
    db.session.commit()
    flash('Message deleted.', 'success')
    return redirect(url_for('admin.messages'))


@admin_bp.route('/settings')
@admin_required
def settings():
    return render_template('admin/settings.html')
