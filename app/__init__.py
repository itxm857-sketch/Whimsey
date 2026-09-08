from flask import Flask, render_template, session
from dotenv import load_dotenv
from flask_login import current_user
from flask_session import Session
from .extensions import db, migrate, csrf, login_manager
from .models import User, Category, Message


def create_app(config_object=None):
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(config_object or 'config.Config')
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    app.config['SESSION_SQLALCHEMY'] = db
    Session(app)

    from .routes.auth import auth_bp
    from .routes.shop import shop_bp
    from .routes.cart import cart_bp
    from .routes.orders import orders_bp
    from .routes.admin import admin_bp
    from .routes.messages import messages_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(messages_bp)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (ValueError, TypeError):
            return None

    @app.context_processor
    def inject_globals():
        cart = session.get('cart', {})
        cart_count = sum(int(q) for q in cart.values()) if cart else 0
        categories = Category.query.order_by(Category.name.asc()).all()
        unread = Message.query.filter_by(is_read=False).count() if current_user.is_authenticated and current_user.role == 'admin' else 0
        return {'cart_count': cart_count, 'nav_categories': categories, 'unread_messages': unread}

    @app.errorhandler(404)
    def not_found(_):
        return render_template('error.html', code=404, title='Page not found', message="We couldn't find the page you're looking for."), 404

    @app.errorhandler(403)
    def forbidden(_):
        return render_template('error.html', code=403, title='Access denied', message="You don't have permission to access this page."), 403

    @app.errorhandler(500)
    def server_error(_):
        db.session.rollback()
        return render_template('error.html', code=500, title='Something went wrong', message='Please try again in a moment.'), 500

    return app
