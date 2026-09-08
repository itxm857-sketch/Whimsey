"""initial Whimsy schema

Revision ID: 0001_initial
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('flask_sessions', sa.Column('id', sa.String(length=255), nullable=False), sa.Column('data', sa.LargeBinary(), nullable=True), sa.Column('expiry', sa.DateTime(), nullable=True), sa.PrimaryKeyConstraint('id'))
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False), sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False), sa.Column('phone', sa.String(length=40), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False), sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False), sa.PrimaryKeyConstraint('id'))
    op.create_index('ix_users_email', 'users', ['email'], unique=True); op.create_index('ix_users_role','users',['role']); op.create_index('ix_users_is_active','users',['is_active'])
    op.create_table('categories', sa.Column('id',sa.Integer(),nullable=False), sa.Column('name',sa.String(120),nullable=False), sa.Column('slug',sa.String(140),nullable=False), sa.Column('description',sa.Text(),nullable=True), sa.Column('created_at',sa.DateTime(timezone=True),nullable=False), sa.PrimaryKeyConstraint('id'))
    op.create_index('ix_categories_slug','categories',['slug'],unique=True); op.create_index('ix_categories_name','categories',['name'],unique=True)
    op.create_table('products',
        sa.Column('id',sa.Integer(),nullable=False), sa.Column('name',sa.String(180),nullable=False), sa.Column('slug',sa.String(200),nullable=False),
        sa.Column('description',sa.Text(),nullable=True), sa.Column('price',sa.Numeric(12,2),nullable=False), sa.Column('sale_price',sa.Numeric(12,2),nullable=True),
        sa.Column('stock',sa.Integer(),nullable=False), sa.Column('low_stock_threshold',sa.Integer(),nullable=False), sa.Column('sku',sa.String(80),nullable=False),
        sa.Column('category_id',sa.Integer(),nullable=True), sa.Column('image_url',sa.String(1000),nullable=True), sa.Column('additional_images',sa.JSON(),nullable=False),
        sa.Column('featured',sa.Boolean(),nullable=False), sa.Column('active',sa.Boolean(),nullable=False), sa.Column('views',sa.Integer(),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False), sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(['category_id'],['categories.id'],ondelete='SET NULL'), sa.PrimaryKeyConstraint('id'))
    op.create_index('ix_products_slug','products',['slug'],unique=True); op.create_index('ix_products_sku','products',['sku'],unique=True); op.create_index('ix_products_category_id','products',['category_id']); op.create_index('ix_products_featured','products',['featured']); op.create_index('ix_products_active','products',['active']); op.create_index('ix_products_created_at','products',['created_at'])
    op.create_table('orders',
        sa.Column('id',sa.Integer(),nullable=False), sa.Column('order_number',sa.String(40),nullable=False), sa.Column('user_id',sa.Integer(),nullable=True),
        sa.Column('customer_name',sa.String(120),nullable=False), sa.Column('email',sa.String(255),nullable=False), sa.Column('phone',sa.String(40),nullable=False),
        sa.Column('address',sa.Text(),nullable=False), sa.Column('city',sa.String(120),nullable=False), sa.Column('postal_code',sa.String(30),nullable=True),
        sa.Column('subtotal',sa.Numeric(12,2),nullable=False), sa.Column('shipping_fee',sa.Numeric(12,2),nullable=False), sa.Column('total',sa.Numeric(12,2),nullable=False),
        sa.Column('status',sa.String(30),nullable=False), sa.Column('stock_deducted',sa.Boolean(),nullable=False), sa.Column('notes',sa.Text(),nullable=True),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False), sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),
        sa.ForeignKeyConstraint(['user_id'],['users.id'],ondelete='SET NULL'), sa.PrimaryKeyConstraint('id'))
    op.create_index('ix_orders_order_number','orders',['order_number'],unique=True); op.create_index('ix_orders_user_id','orders',['user_id']); op.create_index('ix_orders_status','orders',['status']); op.create_index('ix_orders_created_at','orders',['created_at'])
    op.create_table('order_items', sa.Column('id',sa.Integer(),nullable=False), sa.Column('order_id',sa.Integer(),nullable=False), sa.Column('product_id',sa.Integer(),nullable=True), sa.Column('product_name_snapshot',sa.String(180),nullable=False), sa.Column('price_snapshot',sa.Numeric(12,2),nullable=False), sa.Column('quantity',sa.Integer(),nullable=False), sa.Column('subtotal',sa.Numeric(12,2),nullable=False), sa.ForeignKeyConstraint(['order_id'],['orders.id'],ondelete='CASCADE'), sa.ForeignKeyConstraint(['product_id'],['products.id'],ondelete='SET NULL'), sa.PrimaryKeyConstraint('id'))
    op.create_index('ix_order_items_order_id','order_items',['order_id']); op.create_index('ix_order_items_product_id','order_items',['product_id'])
    op.create_table('messages', sa.Column('id',sa.Integer(),nullable=False), sa.Column('name',sa.String(120),nullable=False), sa.Column('email',sa.String(255),nullable=False), sa.Column('phone',sa.String(40),nullable=True), sa.Column('subject',sa.String(200),nullable=False), sa.Column('message',sa.Text(),nullable=False), sa.Column('is_read',sa.Boolean(),nullable=False), sa.Column('created_at',sa.DateTime(timezone=True),nullable=False), sa.PrimaryKeyConstraint('id'))
    op.create_index('ix_messages_is_read','messages',['is_read']); op.create_index('ix_messages_created_at','messages',['created_at'])
    op.create_table('site_settings', sa.Column('id',sa.Integer(),nullable=False), sa.Column('key',sa.String(80),nullable=False), sa.Column('value',sa.Text(),nullable=True), sa.PrimaryKeyConstraint('id'))
    op.create_index('ix_site_settings_key','site_settings',['key'],unique=True)

def downgrade():
    op.drop_table('flask_sessions')
    op.drop_index('ix_site_settings_key', table_name='site_settings'); op.drop_table('site_settings')
    op.drop_index('ix_messages_created_at', table_name='messages'); op.drop_index('ix_messages_is_read', table_name='messages'); op.drop_table('messages')
    op.drop_index('ix_order_items_product_id', table_name='order_items'); op.drop_index('ix_order_items_order_id', table_name='order_items'); op.drop_table('order_items')
    op.drop_index('ix_orders_created_at', table_name='orders'); op.drop_index('ix_orders_status', table_name='orders'); op.drop_index('ix_orders_user_id', table_name='orders'); op.drop_index('ix_orders_order_number', table_name='orders'); op.drop_table('orders')
    op.drop_index('ix_products_created_at', table_name='products'); op.drop_index('ix_products_active', table_name='products'); op.drop_index('ix_products_featured', table_name='products'); op.drop_index('ix_products_category_id', table_name='products'); op.drop_index('ix_products_sku', table_name='products'); op.drop_index('ix_products_slug', table_name='products'); op.drop_table('products')
    op.drop_index('ix_categories_name', table_name='categories'); op.drop_index('ix_categories_slug', table_name='categories'); op.drop_table('categories')
    op.drop_index('ix_users_is_active', table_name='users'); op.drop_index('ix_users_role', table_name='users'); op.drop_index('ix_users_email', table_name='users'); op.drop_table('users')
