from decimal import Decimal
from flask import Blueprint, abort, render_template, request
from sqlalchemy import or_, desc, asc
from ..extensions import db
from ..models import Product, Category

shop_bp = Blueprint('shop', __name__)


@shop_bp.route('/')
def home():
    featured = Product.query.filter_by(active=True, featured=True).order_by(desc(Product.created_at)).limit(8).all()
    new_arrivals = Product.query.filter_by(active=True).order_by(desc(Product.created_at)).limit(8).all()
    popular = Product.query.filter_by(active=True).order_by(desc(Product.views)).limit(8).all()
    return render_template('index.html', featured=featured, new_arrivals=new_arrivals, popular=popular)


@shop_bp.route('/shop')
def shop():
    query = Product.query.filter_by(active=True)
    q = request.args.get('q', '').strip()
    category_slug = request.args.get('category', '').strip()
    min_price = request.args.get('min_price', '').strip()
    max_price = request.args.get('max_price', '').strip()
    sort = request.args.get('sort', 'newest')
    if q:
        term = f'%{q}%'
        query = query.outerjoin(Category).filter(or_(Product.name.ilike(term), Product.sku.ilike(term), Category.name.ilike(term)))
    if category_slug:
        query = query.join(Category).filter(Category.slug == category_slug)
    try:
        if min_price: query = query.filter(Product.price >= Decimal(min_price))
        if max_price: query = query.filter(Product.price <= Decimal(max_price))
    except Exception:
        pass
    if sort == 'price_low': query = query.order_by(asc(Product.sale_price).nullslast(), asc(Product.price))
    elif sort == 'price_high': query = query.order_by(desc(Product.sale_price).nullslast(), desc(Product.price))
    elif sort == 'popular': query = query.order_by(desc(Product.views), desc(Product.created_at))
    else: query = query.order_by(desc(Product.created_at))
    page = query.paginate(page=request.args.get('page', 1, type=int), per_page=12, error_out=False)
    categories = Category.query.order_by(Category.name).all()
    return render_template('shop.html', products=page.items, pagination=page, categories=categories, q=q, category_slug=category_slug, sort=sort, min_price=min_price, max_price=max_price)


@shop_bp.route('/category/<slug>')
def category(slug):
    cat = Category.query.filter_by(slug=slug).first_or_404()
    products = cat.products.filter_by(active=True).order_by(Product.created_at.desc()).all()
    return render_template('category.html', category=cat, products=products)


@shop_bp.route('/product/<slug>')
def product(slug):
    product = Product.query.filter_by(slug=slug, active=True).first_or_404()
    product.views += 1
    db.session.commit()
    related = Product.query.filter(Product.active.is_(True), Product.id != product.id, Product.category_id == product.category_id).order_by(desc(Product.created_at)).limit(4).all()
    return render_template('product.html', product=product, related=related)


@shop_bp.route('/about')
def about():
    return render_template('about.html')
