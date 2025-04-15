import streamlit as st
import pandas as pd
import datetime
import uuid
import os
import base64
from reportlab.lib import colors
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A3
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import base64
import warnings
import json
from datetime import date
import pymongo
import pandas as pd
import plotly.graph_objects as go

# Suppress the ScriptRunContext warnings
warnings.filterwarnings('ignore', message='.*missing ScriptRunContext.*')

# Set page configuration
st.set_page_config(
    page_title="Hệ Thống Quản Lý Tiệm Bánh",
    page_icon="🍰",
    layout="wide"
)

def init_mongodb_client():
    """Initialize MongoDB client using Streamlit secrets"""
    try:
        if "mongodb" in st.secrets:
            # Get connection details from secrets
            connection_string = st.secrets["mongodb"]["connection_string"]
            database_name = st.secrets["mongodb"]["database"]
            
            # Create MongoDB client
            client = pymongo.MongoClient(connection_string)
            db = client[database_name]
            
            # Store in session state
            st.session_state.mongo_client = client
            st.session_state.mongo_db = db
            
            if show_debug:
                st.sidebar.success(f"Connected to MongoDB Atlas: {database_name}")
            
            return client, db
        else:
            if show_debug:
                st.sidebar.warning("MongoDB credentials not found in secrets. Using session state only.")
            return None, None
    except Exception as e:
        if show_debug:
            st.sidebar.error(f"Error initializing MongoDB: {str(e)}")
        return None, None

def save_dataframe(df, collection_name):
    """Save a dataframe to MongoDB or session state"""
    try:
        # Try to save to MongoDB if client is available
        if "mongo_client" in st.session_state and "mongo_db" in st.session_state:
            db = st.session_state.mongo_db
            
            # Convert dataframe to records
            records = df.to_dict(orient='records')
            
            # Get collection name (remove .csv extension)
            coll_name = collection_name.replace('.csv', '')
            collection = db[coll_name]
            
            # Delete existing documents and insert new ones
            collection.delete_many({})
            if records:
                collection.insert_many(records)
            
            if show_debug:
                st.sidebar.write(f"Saved {len(records)} rows to MongoDB: {coll_name}")
            
            # Also save to session state as backup
            key = collection_name.replace('.csv', '')
            st.session_state[key] = df
            
            return True
        else:
            # Save to session state only
            key = collection_name.replace('.csv', '')
            st.session_state[key] = df
            
            if show_debug:
                st.sidebar.write(f"Saved {len(df)} rows to session state: {key}")
            
            return True
    except Exception as e:
        print(f"Error saving {collection_name}: {e}")
        st.error(f"Failed to save {collection_name}: {e}")
        
        # Try to save to session state as fallback
        try:
            key = collection_name.replace('.csv', '')
            st.session_state[key] = df
            return True
        except:
            return False

def load_dataframe(collection_name, default_df):
    """Load a dataframe from MongoDB or session state, or return default if not found"""
    try:
        # Try to load from MongoDB if client is available
        if "mongo_client" in st.session_state and "mongo_db" in st.session_state:
            db = st.session_state.mongo_db
            
            # Get collection name (remove .csv extension)
            coll_name = collection_name.replace('.csv', '')
            
            try:
                # Try to get data from MongoDB
                collection = db[coll_name]
                data = list(collection.find({}, {'_id': 0}))  # Exclude MongoDB _id field
                
                if data:
                    # Convert to DataFrame
                    df = pd.DataFrame(data)
                    
                    # Save to session state as a backup
                    key = collection_name.replace('.csv', '')
                    st.session_state[key] = df
                    
                    if show_debug:
                        st.sidebar.write(f"Loaded {len(df)} rows from MongoDB: {coll_name}")
                    
                    return df
                else:
                    # If no data in MongoDB, check session state
                    if show_debug:
                        st.sidebar.write(f"No data found in MongoDB: {coll_name}, checking session state")
                    
                    # Try to load from session state
                    key = collection_name.replace('.csv', '')
                    if key in st.session_state:
                        df = st.session_state[key]
                        if len(df) > 0:
                            if show_debug:
                                st.sidebar.write(f"Loaded {len(df)} rows from session state: {key}")
                            return df
                    
                    # If not in session state either, return default
                    if show_debug:
                        st.sidebar.write(f"No data found in session state, using default")
                    
                    return default_df.copy()
            except Exception as e:
                # Handle MongoDB errors
                if show_debug:
                    st.sidebar.error(f"Error reading from MongoDB: {str(e)}")
                
                # Try to load from session state
                key = collection_name.replace('.csv', '')
                if key in st.session_state:
                    df = st.session_state[key]
                    if len(df) > 0:
                        if show_debug:
                            st.sidebar.write(f"Loaded {len(df)} rows from session state: {key}")
                        return df
                
                # If not in session state, return default
                return default_df.copy()
        else:
            # Try to load from session state
            key = collection_name.replace('.csv', '')
            if key in st.session_state:
                df = st.session_state[key]
                if len(df) > 0:
                    if show_debug:
                        st.sidebar.write(f"Loaded {len(df)} rows from session state: {key}")
                    return df
            
            # If not in session state, return default
            return default_df.copy()
            
    except Exception as e:
        print(f"Error loading {collection_name}: {e}")
        st.error(f"Failed to load {collection_name}: {e}")
        return default_df.copy()
    
# Add a toggle to show debug information
show_debug = st.sidebar.checkbox("Show Debug Info", value=False)

# Initialize MongoDB client
if "mongo_client" not in st.session_state or "mongo_db" not in st.session_state:
    mongo_client, mongo_db = init_mongodb_client()
else:
    mongo_client = st.session_state.mongo_client
    mongo_db = st.session_state.mongo_db

if show_debug:
    st.sidebar.write("### Debug Information")
    
    # Show storage info
    if mongo_client is not None and mongo_db is not None:
        st.sidebar.write(f"Using MongoDB Atlas for storage: {mongo_db.name}")
    else:
        st.sidebar.write("Using session state for storage")

def ensure_mongodb_connection():
    """Check if MongoDB database is accessible"""
    if "mongo_client" in st.session_state and "mongo_db" in st.session_state:
        try:
            mongo_client = st.session_state.mongo_client
            mongo_db = st.session_state.mongo_db
            
            # Check if connection is alive
            info = mongo_client.server_info()
            
            if show_debug:
                st.sidebar.write(f"MongoDB database is accessible: {mongo_db.name}")
            
            return True
        except Exception as e:
            if show_debug:
                st.sidebar.error(f"Error accessing MongoDB: {str(e)}")
            return False
    return False

# Call this function after initialization
ensure_mongodb_connection()


# Default dataframes (will be used if files don't exist)
default_products = pd.DataFrame(columns=[
    'product_id', 'name', 'price', 'category', 'unit' 
])

default_materials = pd.DataFrame(columns=[
    'material_id', 'name', 'unit', 'quantity', 'price_per_unit', 'used_quantity'
])

default_recipes = pd.DataFrame(columns=[
    'product_id', 'material_id', 'quantity'
])

default_orders = pd.DataFrame(columns=[
    'order_id', 'date', 'customer_name', 'customer_phone', 'total_amount', 'status'
])

default_order_items = pd.DataFrame(columns=[
    'order_id', 'product_id', 'quantity', 'price', 'subtotal'
])

default_invoices = pd.DataFrame(columns=[
    'invoice_id', 'order_id', 'date', 'customer_name', 'total_amount', 'payment_method'
])

default_income = pd.DataFrame(columns=[
    'date', 'total_sales', 'cost_of_goods', 'profit', 'other_costs', 'depreciation_costs', 'material_import_costs'
])

default_material_costs = pd.DataFrame(columns=[
    'date', 'material_id', 'quantity', 'total_cost', 'supplier'
])

default_invoice_status = pd.DataFrame(columns=[
    'invoice_id', 'is_completed', 'completion_date', 'notes', 'payment_status'
])

default_labor_costs = pd.DataFrame(columns=[
    'date', 'worker_name', 'description', 'hours', 'unit_rate', 'total_cost', 'notes'
])

# Load data from files or use defaults
if 'products' not in st.session_state:
    st.session_state.products = load_dataframe("products.csv", default_products)

if 'materials' not in st.session_state:
    st.session_state.materials = load_dataframe("materials.csv", default_materials)

if 'recipes' not in st.session_state:
    st.session_state.recipes = load_dataframe("recipes.csv", default_recipes)

if 'orders' not in st.session_state:
    st.session_state.orders = load_dataframe("orders.csv", default_orders)

if 'order_items' not in st.session_state:
    st.session_state.order_items = load_dataframe("order_items.csv", default_order_items)

if 'invoices' not in st.session_state:
    st.session_state.invoices = load_dataframe("invoices.csv", default_invoices)

if 'income' not in st.session_state:
    st.session_state.income = load_dataframe("income.csv", default_income)

if 'material_costs' not in st.session_state:
    st.session_state.material_costs = load_dataframe("material_costs.csv", default_material_costs)

if 'invoice_status' not in st.session_state:
    st.session_state.invoice_status = load_dataframe("invoice_status.csv", default_invoice_status)

if 'labor_costs' not in st.session_state:
    st.session_state.labor_costs = load_dataframe("labor_costs.csv", default_labor_costs)

# Function to ensure we have Unicode support for Vietnamese
def setup_vietnamese_font():
    try:
        # Use relative paths for Streamlit Cloud
        roboto_base_dir = "fonts/static"
        
        try:
            regular_path = f"{roboto_base_dir}/Roboto-Regular.ttf"
            bold_path = f"{roboto_base_dir}/Roboto-Bold.ttf"
            
            # Check if fonts exist
            if os.path.exists(regular_path) and os.path.exists(bold_path):
                # Register the regular font
                pdfmetrics.registerFont(TTFont('Roboto', regular_path))
                # Register the bold font
                pdfmetrics.registerFont(TTFont('Roboto-Bold', bold_path))
                return 'Roboto'
            else:
                # Fall back to Helvetica if fonts don't exist
                return 'Helvetica'
                
        except Exception as e:
            print(f"Font error: {e}")
            # Fall back to Helvetica if there's any issue
            return 'Helvetica'
            
    except Exception as e:
        print(f"Font setup error: {e}")
        # Fall back to Helvetica
        return 'Helvetica'

def save_all_data():
    """Save all dataframes to CSV files"""
    save_dataframe(st.session_state.products, "products.csv")
    save_dataframe(st.session_state.materials, "materials.csv")
    save_dataframe(st.session_state.recipes, "recipes.csv")
    save_dataframe(st.session_state.orders, "orders.csv")
    save_dataframe(st.session_state.order_items, "order_items.csv")
    save_dataframe(st.session_state.invoices, "invoices.csv")
    save_dataframe(st.session_state.income, "income.csv")
    
    if 'material_costs' in st.session_state:
        save_dataframe(st.session_state.material_costs, "material_costs.csv")
    
    if 'invoice_status' in st.session_state:
        save_dataframe(st.session_state.invoice_status, "invoice_status.csv")
    
    if 'product_costs' in st.session_state:
        save_dataframe(st.session_state.product_costs, "product_costs.csv") 

    if 'labor_costs' in st.session_state:
        save_dataframe(st.session_state.labor_costs, "labor_costs.csv")

# Function to update material quantities after an order
def update_materials_after_order(order_id):
    """
    Cập nhật số lượng nguyên liệu sau khi tạo đơn hàng
    Không cho phép số lượng nguyên liệu âm
    """
    # Get order items
    order_items_df = st.session_state.order_items[st.session_state.order_items['order_id'] == order_id]
    
    # For each order item, reduce materials according to recipe
    for _, item in order_items_df.iterrows():
        product_id = item['product_id']
        order_quantity = item['quantity']
        
        # Get recipe for this product
        product_recipe = st.session_state.recipes[st.session_state.recipes['product_id'] == product_id]
        
        # For each material in the recipe, reduce quantity and track usage
        for _, recipe_item in product_recipe.iterrows():
            material_id = recipe_item['material_id']
            material_quantity_needed = recipe_item['quantity'] * order_quantity
            
            # Update material quantity
            material_idx = st.session_state.materials[st.session_state.materials['material_id'] == material_id].index[0]
            current_quantity = st.session_state.materials.at[material_idx, 'quantity']
            
            # Đảm bảo số lượng không âm
            if current_quantity < material_quantity_needed:
                # Không nên xảy ra vì đã kiểm tra trước khi đến đây, nhưng để chắc chắn
                st.error(f"Lỗi: Không đủ nguyên liệu {material_id} để thực hiện đơn hàng!")
                return False
            
            st.session_state.materials.at[material_idx, 'quantity'] -= material_quantity_needed
            
            # Update used quantity
            st.session_state.materials.at[material_idx, 'used_quantity'] += material_quantity_needed
    
    return True

def calculate_cost_of_goods(order_id):
    """
    Tính toán chi phí cho một đơn hàng và phân tách thành chi phí nguyên liệu và chi phí khác
    Trả về dict chứa chi phí nguyên liệu, chi phí khác và tổng chi phí
    """
    total_material_cost = 0
    total_other_cost = 0  # Bao gồm chi phí khác và chi phí khấu hao
    
    order_items_df = st.session_state.order_items[st.session_state.order_items['order_id'] == order_id]
    
    for _, item in order_items_df.iterrows():
        product_id = item['product_id']
        order_quantity = item['quantity']
        
        # Lấy chi phí từ thông tin sản phẩm (nếu có)
        product_other_fee = 0
        product_depreciation_fee = 0
        
        if 'product_costs' in st.session_state and not st.session_state.product_costs.empty:
            product_cost_data = st.session_state.product_costs[
                st.session_state.product_costs['product_id'] == product_id
            ]
            
            if not product_cost_data.empty:
                # Ensure column names are accessed correctly
                if 'other_fee' in product_cost_data.columns:
                    product_other_fee = product_cost_data['other_fee'].iloc[0] * order_quantity
                
                # Make sure we're accessing the correct column name for depreciation fee
                if 'Depreciation_fee' in product_cost_data.columns:  # Note the capital 'D'
                    product_depreciation_fee = product_cost_data['Depreciation_fee'].iloc[0] * order_quantity
        
        # Cộng vào tổng chi phí khác
        total_other_cost += product_other_fee + product_depreciation_fee
        
        # Tính chi phí nguyên liệu dựa vào công thức
        product_material_cost = 0
        product_recipe = st.session_state.recipes[st.session_state.recipes['product_id'] == product_id]
        
        for _, recipe_item in product_recipe.iterrows():
            material_id = recipe_item['material_id']
            material_quantity = recipe_item['quantity'] * order_quantity
            
            # Lấy giá nguyên liệu
            material_data = st.session_state.materials[
                st.session_state.materials['material_id'] == material_id
            ]
            
            if not material_data.empty:
                material_price = material_data['price_per_unit'].iloc[0]
                product_material_cost += material_quantity * material_price
        
        total_material_cost += product_material_cost
    
    # Trả về dict chứa chi tiết chi phí
    return {
        'material_cost': total_material_cost,
        'other_cost': total_other_cost,
        'total_cost': total_material_cost + total_other_cost
    }

def check_sufficient_materials(selected_products, quantities):
    """
    Kiểm tra xem có đủ nguyên liệu để hoàn thành đơn hàng hay không
    Trả về True nếu đủ, False nếu không đủ, cùng với danh sách nguyên liệu thiếu
    """
    # Tính toán tổng nguyên liệu cần thiết cho đơn hàng
    required_materials = {}
    
    for product, quantity in zip(selected_products, quantities):
        product_id = product['product_id']
        # Lấy công thức của sản phẩm
        product_recipe = st.session_state.recipes[st.session_state.recipes['product_id'] == product_id]
        
        # Cho mỗi nguyên liệu trong công thức
        for _, recipe_item in product_recipe.iterrows():
            material_id = recipe_item['material_id']
            material_quantity_needed = recipe_item['quantity'] * quantity
            
            # Cộng dồn vào tổng nguyên liệu cần thiết
            if material_id in required_materials:
                required_materials[material_id] += material_quantity_needed
            else:
                required_materials[material_id] = material_quantity_needed
    
    # Kiểm tra xem có đủ nguyên liệu trong kho không
    insufficient_materials = []
    
    for material_id, required_quantity in required_materials.items():
        # Lấy thông tin nguyên liệu
        material_data = st.session_state.materials[st.session_state.materials['material_id'] == material_id]
        
        if not material_data.empty:
            available_quantity = material_data['quantity'].iloc[0]
            material_name = material_data['name'].iloc[0]
            material_unit = material_data['unit'].iloc[0]
            
            # So sánh số lượng cần với số lượng hiện có
            if required_quantity > available_quantity:
                insufficient_materials.append({
                    'id': material_id,
                    'name': material_name,
                    'unit': material_unit,
                    'required': required_quantity,
                    'available': available_quantity,
                    'shortage': required_quantity - available_quantity
                })
    
    return len(insufficient_materials) == 0, insufficient_materials

# Function to update income records after completing an order
def update_income(order_id):
    order_data = st.session_state.orders[st.session_state.orders['order_id'] == order_id].iloc[0]
    order_date = order_data['date']
    
    # Get product amount 
    product_amount = float(order_data['total_amount'])
    
    # Lấy thông tin giảm giá (nếu có)
    discount_amount = order_data.get('discount_amount', 0)
    
    # Calculate total revenue (không bao gồm phí vận chuyển nữa)
    total_amount = product_amount
    
    # Calculate cost of materials used (đổi tên từ cost_of_goods)
    try:
        cost_of_goods_value = calculate_cost_of_goods(order_id)
        if isinstance(cost_of_goods_value, dict):
            # Nếu là dict, lấy giá trị từ dict
            if len(cost_of_goods_value) > 0:
                material_cost = float(cost_of_goods_value.get('material_cost', 0))
                cost_of_goods = material_cost  # Chỉ lấy chi phí nguyên liệu
            else:
                cost_of_goods = 0.0
        else:
            # Nếu không phải dict, chuyển sang float
            cost_of_goods = float(cost_of_goods_value)
    except Exception as e:
        if show_debug:
            st.sidebar.error(f"Error calculating material cost: {str(e)}")
        cost_of_goods = 0.0
    
    # Lấy thông tin chi phí khác và chi phí khấu hao từ product_costs
    other_costs = 0.0
    depreciation_costs = 0.0
    
    # Lấy danh sách sản phẩm trong đơn hàng
    order_items_df = st.session_state.order_items[st.session_state.order_items['order_id'] == order_id]
    
    # Nếu có theo dõi chi phí sản phẩm
    if 'product_costs' in st.session_state and not st.session_state.product_costs.empty:
        for _, item in order_items_df.iterrows():
            product_id = item['product_id']
            quantity = float(item['quantity'])
            
            # Tìm thông tin chi phí của sản phẩm
            product_cost_data = st.session_state.product_costs[st.session_state.product_costs['product_id'] == product_id]
            
            if not product_cost_data.empty:
                # Lấy chi phí khác
                if 'other_fee' in product_cost_data.columns:
                    try:
                        other_fee = float(product_cost_data['other_fee'].iloc[0])
                        other_costs += other_fee * quantity
                    except Exception as e:
                        if show_debug:
                            st.sidebar.error(f"Error converting other_fee: {str(e)}")
                
                # Lấy chi phí khấu hao
                if 'Depreciation_fee' in product_cost_data.columns:
                    try:
                        depreciation_fee = float(product_cost_data['Depreciation_fee'].iloc[0])
                        depreciation_costs += depreciation_fee * quantity
                    except Exception as e:
                        if show_debug:
                            st.sidebar.error(f"Error converting Depreciation_fee: {str(e)}")
    
    # Calculate profit (lợi nhuận trước khi trừ các chi phí nhập hàng và nhân công)
    try:
        profit = float(total_amount) - float(cost_of_goods) - float(other_costs) - float(depreciation_costs)
    except Exception as e:
        if show_debug:
            st.sidebar.error(f"Error calculating profit: {str(e)}")
        profit = 0.0
    
    # Check if date already exists in income DataFrame
    if order_date in st.session_state.income['date'].values:
        idx = st.session_state.income[st.session_state.income['date'] == order_date].index[0]
        st.session_state.income.at[idx, 'total_sales'] += total_amount
        st.session_state.income.at[idx, 'cost_of_goods'] += cost_of_goods
        st.session_state.income.at[idx, 'profit'] += profit
        
        # Track other costs
        if 'other_costs' in st.session_state.income.columns:
            st.session_state.income.at[idx, 'other_costs'] += other_costs
        else:
            st.session_state.income['other_costs'] = 0
            st.session_state.income.at[idx, 'other_costs'] = other_costs
            
        # Track depreciation costs
        if 'depreciation_costs' in st.session_state.income.columns:
            st.session_state.income.at[idx, 'depreciation_costs'] += depreciation_costs
        else:
            st.session_state.income['depreciation_costs'] = 0
            st.session_state.income.at[idx, 'depreciation_costs'] = depreciation_costs
            
        # Track discount costs - THÊM MỚI
        if 'discount_costs' in st.session_state.income.columns:
            st.session_state.income.at[idx, 'discount_costs'] += discount_amount
        else:
            st.session_state.income['discount_costs'] = 0
            st.session_state.income.at[idx, 'discount_costs'] = discount_amount
    else:
        # Create new row for this date
        if 'other_costs' not in st.session_state.income.columns:
            # Add other costs column if it doesn't exist
            st.session_state.income['other_costs'] = 0
            
        if 'depreciation_costs' not in st.session_state.income.columns:
            # Add depreciation costs column if it doesn't exist
            st.session_state.income['depreciation_costs'] = 0
            
        if 'discount_costs' not in st.session_state.income.columns:
            # Add discount costs column if it doesn't exist - THÊM MỚI
            st.session_state.income['discount_costs'] = 0
            
        new_row = pd.DataFrame({
            'date': [order_date],
            'total_sales': [total_amount],
            'cost_of_goods': [cost_of_goods],
            'profit': [profit],
            'other_costs': [other_costs],
            'depreciation_costs': [depreciation_costs],
            'discount_costs': [discount_amount]  # THÊM MỚI
        })
        
        st.session_state.income = pd.concat([st.session_state.income, new_row], ignore_index=True)


# Cập nhật hàm adjust_income_after_delete_invoice để giữ lại chi phí khấu hao và chi phí nguyên liệu đã sử dụng
# Đơn giản hóa cách xử lý khi xóa hóa đơn

def adjust_income_after_delete_invoice(invoice_id, order_id):
    """Điều chỉnh dữ liệu doanh thu sau khi xóa hóa đơn - xóa các chi phí liên quan đến đơn hàng
    nhưng giữ lại chi phí nhập hàng (đã được theo dõi riêng trong bảng material_costs)"""
    try:
        # Lấy thông tin hóa đơn đã xóa
        order_data = st.session_state.orders[st.session_state.orders['order_id'] == order_id]
        
        if order_data.empty:
            return False
            
        order_data = order_data.iloc[0]
        order_date = order_data['date']
        
        # Lấy thông tin chi tiết đơn hàng
        order_items = st.session_state.order_items[st.session_state.order_items['order_id'] == order_id]
        
        if order_items.empty:
            return False
            
        # 1. Hoàn lại nguyên liệu đã sử dụng
        restore_materials_after_delete_order(order_id)
        
        # 2. Xóa dữ liệu doanh thu liên quan đến đơn hàng (chi phí nhập hàng được theo dõi
        # trong bảng material_costs riêng và không bị ảnh hưởng)
        if order_date in st.session_state.income['date'].values:
            # Tìm dòng doanh thu ứng với ngày của hóa đơn
            income_rows = st.session_state.income[st.session_state.income['date'] == order_date]
            
            if not income_rows.empty:
                idx = income_rows.index[0]
                
                # Lấy tổng giá trị đơn hàng
                total_amount = float(order_data['total_amount'])
                
                # Lấy giá trị giảm giá (nếu có) - THÊM MỚI
                discount_amount = float(order_data.get('discount_amount', 0))
                
                # Tính chi phí của đơn hàng
                try:
                    cost_result = calculate_cost_of_goods(order_id)
                    if isinstance(cost_result, dict):
                        # CHỖ NÀY CÓ SỬA - chỉ lấy chi phí nguyên liệu
                        order_cost_of_goods = float(cost_result.get('material_cost', 0))
                    else:
                        order_cost_of_goods = float(cost_result)
                except Exception as e:
                    if show_debug:
                        st.sidebar.error(f"Error calculating cost_of_goods for deletion: {str(e)}")
                    order_cost_of_goods = 0
                
                # Tính chi phí khác và chi phí khấu hao từ product_costs
                order_other_costs = 0
                order_depreciation_costs = 0
                for _, item in order_items.iterrows():
                    product_id = item['product_id']
                    quantity = float(item['quantity'])
                    
                    # Lấy thông tin chi phí khác và chi phí khấu hao sản phẩm
                    if 'product_costs' in st.session_state and not st.session_state.product_costs.empty:
                        product_cost_data = st.session_state.product_costs[st.session_state.product_costs['product_id'] == product_id]
                        
                        if not product_cost_data.empty:
                            # Chi phí khác
                            if 'other_fee' in product_cost_data.columns:
                                try:
                                    other_fee = float(product_cost_data['other_fee'].iloc[0])
                                    order_other_costs += other_fee * quantity
                                except Exception as e:
                                    if show_debug:
                                        st.sidebar.error(f"Error calculating other costs: {str(e)}")
                            
                            # Chi phí khấu hao
                            if 'Depreciation_fee' in product_cost_data.columns:
                                try:
                                    depreciation_fee = float(product_cost_data['Depreciation_fee'].iloc[0])
                                    order_depreciation_costs += depreciation_fee * quantity
                                except Exception as e:
                                    if show_debug:
                                        st.sidebar.error(f"Error calculating depreciation: {str(e)}")
                
                # Tính lợi nhuận của đơn hàng
                order_profit = total_amount - order_cost_of_goods - order_other_costs - order_depreciation_costs
                
                # Trừ các giá trị từ dòng doanh thu
                st.session_state.income.at[idx, 'total_sales'] -= total_amount
                st.session_state.income.at[idx, 'cost_of_goods'] -= order_cost_of_goods
                st.session_state.income.at[idx, 'profit'] -= order_profit
                
                # Trừ chi phí khác nếu có theo dõi
                if 'other_costs' in st.session_state.income.columns:
                    st.session_state.income.at[idx, 'other_costs'] -= order_other_costs
                
                # Trừ chi phí khấu hao nếu có theo dõi
                if 'depreciation_costs' in st.session_state.income.columns:
                    st.session_state.income.at[idx, 'depreciation_costs'] -= order_depreciation_costs
                    
                # Trừ chi phí giảm giá nếu có theo dõi - THÊM MỚI
                if 'discount_costs' in st.session_state.income.columns:
                    st.session_state.income.at[idx, 'discount_costs'] -= discount_amount
                
                # Kiểm tra nếu sau khi trừ, không còn doanh thu nào trong ngày đó
                if st.session_state.income.at[idx, 'total_sales'] <= 0:
                    # Xóa dòng income của ngày đó
                    # Chi phí nhập hàng được theo dõi riêng trong bảng material_costs
                    st.session_state.income = st.session_state.income.drop(idx)
            
            return True
        return False
    except Exception as e:
        if show_debug:
            st.sidebar.error(f"Error in adjust_income_after_delete_invoice: {str(e)}")
        return False

def restore_materials_after_delete_order(order_id):
    """Hoàn lại nguyên liệu đã sử dụng khi xóa đơn hàng"""
    try:
        # Lấy chi tiết đơn hàng
        order_items_df = st.session_state.order_items[st.session_state.order_items['order_id'] == order_id]
        
        # Cho mỗi sản phẩm trong đơn hàng
        for _, item in order_items_df.iterrows():
            product_id = item['product_id']
            order_quantity = item['quantity']
            
            # Lấy công thức của sản phẩm
            product_recipe = st.session_state.recipes[st.session_state.recipes['product_id'] == product_id]
            
            # Cho mỗi nguyên liệu trong công thức, hoàn lại số lượng đã sử dụng
            for _, recipe_item in product_recipe.iterrows():
                material_id = recipe_item['material_id']
                material_quantity_used = recipe_item['quantity'] * order_quantity
                
                # Cập nhật số lượng nguyên liệu (hoàn lại)
                material_rows = st.session_state.materials[st.session_state.materials['material_id'] == material_id]
                if not material_rows.empty:
                    material_idx = material_rows.index[0]
                    
                    # Tăng số lượng nguyên liệu
                    st.session_state.materials.at[material_idx, 'quantity'] += material_quantity_used
                    
                    # Giảm lượng đã sử dụng
                    if 'used_quantity' in st.session_state.materials.columns:
                        st.session_state.materials.at[material_idx, 'used_quantity'] -= material_quantity_used
        
        return True
    except Exception as e:
        if show_debug:
            st.sidebar.error(f"Error restoring materials after delete: {str(e)}")
        return False

def apply_discount_code(code, total_amount):
    """Áp dụng mã giảm giá và trả về số tiền giảm"""
    # Định nghĩa các mã giảm giá hợp lệ và tỷ lệ giảm tương ứng
    valid_codes = {
        "THUXUAN10": 0.10,  # Giảm 10%
        "THUXUAN15": 0.15,  # Giảm 15%
        "THUXUAN20": 0.20,  # Giảm 20%
        "WELCOME": 0.05     # Giảm 5%
    }
    
    # Kiểm tra mã giảm giá
    if code.upper() in valid_codes:
        discount_rate = valid_codes[code.upper()]
        discount_amount = total_amount * discount_rate
        return discount_amount, discount_rate
    else:
        return 0, 0

def generate_invoice_content(invoice_id, order_id, as_pdf=False):
    
    order_data = st.session_state.orders[st.session_state.orders['order_id'] == order_id].iloc[0]
    order_items = st.session_state.order_items[st.session_state.order_items['order_id'] == order_id]
    
    # Get product names
    order_items = order_items.merge(
        st.session_state.products[['product_id', 'name']],
        on='product_id',
        how='left'
    )
    
    # Get shipping fee and customer address from order data (will be 0 if not specified)
    shipping_fee = order_data.get('shipping_fee', 0)
    customer_address = order_data.get('customer_address', '')
    customer_name = order_data['customer_name']
    customer_phone = order_data['customer_phone']
    
    # Calculate subtotal (product amount without shipping)
    subtotal_amount = order_data['total_amount']
    
    # Calculate total amount (with shipping)
    total_amount = subtotal_amount + shipping_fee
    
    # Store information from the original code
    store_name = "THUXUAN CAKE"
    store_address = "Đ/C: Số 10 ngõ 298 Đê La Thành, Đống Đa, Hà Nội"
    store_phone = "ĐT: 0988 159 268"
    
    # PDF version optimized for A3
    buffer = io.BytesIO()
    width, height = A3  # A3 size: 29.7 x 42.0 cm
    
    # Create the PDF with A3 size
    c = canvas.Canvas(buffer, pagesize=A3)
    
    # Set up font for Vietnamese
    font_name = setup_vietnamese_font()
    
    # Function to use proper font with fallback
    def set_font(font_style, size):
        if font_name == 'Roboto':
            try:
                c.setFont(f"Roboto{'-Bold' if font_style == 'bold' else ''}", size)
            except:
                c.setFont(f"Helvetica{'-Bold' if font_style == 'bold' else ''}", size)
        else:
            c.setFont(f"Helvetica{'-Bold' if font_style == 'bold' else ''}", size)
    
    # Simplified page break check - just starts a new page without headers
    def check_page_break(current_y, min_y=7*cm):
        if current_y < min_y:
            c.showPage()  # Just start a new page
            return height - 5*cm  # Return to top of new page
        return current_y
    
    # Adjusted margins for A3 paper
    left_margin = 5*cm
    right_margin = width - 5*cm
    
    # Initialize y position with more space at the top
    y_position = height - 5*cm
    
    # Draw store name (centered) - larger font for A3
    set_font('bold', 60)  # Increased font size for A3
    c.drawCentredString(width/2, y_position, store_name)
    y_position -= 2.5*cm
    
    # Draw store address (centered)
    set_font('normal', 24)  # Increased font size for A3
    c.drawCentredString(width/2, y_position, store_address)
    y_position -= 1.2*cm
    c.drawCentredString(width/2, y_position, store_phone)
    y_position -= 2*cm
    
    # Draw separator line - wider for A3
    c.setLineWidth(2)  # Thicker line for A3
    c.line(left_margin, y_position, right_margin, y_position)
    y_position -= 2*cm
    
    # Bill number with proper alignment for A3
    set_font('bold', 36)  # Increased font size for A3
    c.drawString(left_margin, y_position, "Số hóa đơn:")
    c.drawString(left_margin + 10*cm, y_position, f"#{order_id}#")
    y_position -= 2*cm
    
    # Customer information with proper spacing for A3
    set_font('normal', 30)  # Increased font size for A3
    c.drawString(left_margin, y_position, f"Khách hàng: {customer_name}")
    y_position -= 1.5*cm
    
    # Phone
    y_position = check_page_break(y_position)
    set_font('normal', 30)  # Increased font size for A3
    c.drawString(left_margin, y_position, f"Số điện thoại: {customer_phone}")
    y_position -= 1.5*cm
    
    # Address
    y_position = check_page_break(y_position)
    set_font('normal', 30)  # Increased font size for A3
    c.drawString(left_margin, y_position, f"Địa chỉ: {customer_address}")
    y_position -= 2*cm
    
    # Date
    y_position = check_page_break(y_position)
    set_font('normal', 30)  # Increased font size for A3
    c.drawString(left_margin, y_position, f"Ngày: {order_data['date']}")
    y_position -= 2*cm
    
    # Draw separator line
    y_position = check_page_break(y_position)
    c.setLineWidth(2)
    c.line(left_margin, y_position, right_margin, y_position)
    y_position -= 2*cm
    
    # Column headers with better alignment for A3
    y_position = check_page_break(y_position)
    set_font('bold', 36)  # Increased font size for A3
    c.drawString(left_margin, y_position, "Sản phẩm x SL")
    c.drawRightString(right_margin, y_position, "Giá")
    y_position -= 1.5*cm
    
    # Draw items with better spacing and alignment for A3
    for _, item in order_items.iterrows():
        y_position = check_page_break(y_position)
        set_font('normal', 30)  # Increased font size for A3
        c.drawString(left_margin, y_position, f"{item['name']} x {item['quantity']}")
        # Right-align the price with consistent formatting
        c.drawRightString(right_margin, y_position, f"{item['subtotal']:,.0f}")
        y_position -= 1.5*cm
    
    # Draw separator line
    y_position = check_page_break(y_position)
    c.setLineWidth(2)
    c.line(left_margin, y_position, right_margin, y_position)
    y_position -= 2*cm
    
    # Items/Qty count with proper alignment
    y_position = check_page_break(y_position)
    set_font('normal', 30)  # Increased font size for A3
    c.drawString(left_margin, y_position, "Số lượng mặt hàng/SL")
    c.drawRightString(right_margin, y_position, f"{len(order_items)}/{order_items['quantity'].sum()}")
    y_position -= 2*cm
    
    # Subtotal
    y_position = check_page_break(y_position)
    set_font('normal', 30)
    c.drawString(left_margin, y_position, "Tổng tiền hàng")
    c.drawRightString(right_margin, y_position, f"{subtotal_amount:,.0f}")
    y_position -= 1.5*cm
    
    # Shipping fee
    y_position = check_page_break(y_position)
    set_font('normal', 30)
    c.drawString(left_margin, y_position, "Phí vận chuyển")
    c.drawRightString(right_margin, y_position, f"{shipping_fee:,.0f}")
    y_position -= 1.5*cm
    # Trong hàm generate_invoice_content, thêm đoạn sau để hiển thị thông tin giảm giá

    # Lấy thông tin giảm giá (nếu có)
    discount_amount = order_data.get('discount_amount', 0)
    # Đối với phiên bản PDF, thêm dòng hiển thị giảm giá vào trước tổng thanh toán
    if discount_amount > 0:
        y_position = check_page_break(y_position)
        set_font('normal', 30)
        c.drawString(left_margin, y_position, "Giảm giá")
        c.drawRightString(right_margin, y_position, f"-{discount_amount:,.0f}")
        y_position -= 1.5*cm

    # Total with proper alignment and emphasis
    y_position = check_page_break(y_position)
    set_font('bold', 40)  # Increased font size for A3
    c.drawString(left_margin, y_position, "Tổng thanh toán")
    c.drawRightString(right_margin, y_position, f"{total_amount:,.0f}")
    y_position -= 4*cm  # Tăng khoảng cách sau dòng tổng tiền

    # Check if we need to start a new page for QR code and thank you message
    # Need at least 20cm for QR code, payment info, and thank you message
    if y_position < 20*cm:
        c.showPage()
        y_position = height - 10*cm

    # Add QR code at the center of the page
    try:
        qr_image_path = "assets/qr_code.png"
        
        # Check if file exists before trying to draw it
        if os.path.exists(qr_image_path):
            # Draw QR code with proper positioning
            qr_size = 14*cm  # QR code size
            
            # Calculate position - center of page horizontally
            qr_x = (width - qr_size) / 2
            
            # Thêm dòng separator trước QR code
            c.setLineWidth(1)
            c.line(left_margin, y_position, right_margin, y_position)
            y_position -= 3*cm  # Thêm khoảng cách trước QR code
            
            # Draw QR code centered on the page
            c.drawImage(qr_image_path, qr_x, y_position - 14*cm, width=qr_size, height=qr_size)
            
            # Draw payment information centered below QR code
            set_font('bold', 32)
            c.drawCentredString(width/2, y_position - 15*cm, "Quét để thanh toán")
            
            set_font('normal', 30)
            # Account information
            account_number = "0011000597767"
            account_name = "NGUYỄN VƯƠNG HẰNG"
            c.drawCentredString(width/2, y_position - 16*cm, f"STK: {account_number}")
            c.drawCentredString(width/2, y_position - 17*cm, f"Tên: {account_name}")
            
            # Draw separator line below QR code info
            c.setLineWidth(1)
            c.line(left_margin, y_position - 19*cm, right_margin, y_position - 19*cm)
            
            # Thank you message with proper formatting and quotes
            set_font('normal', 36)  # Increased font size for A3
            c.drawCentredString(width/2, y_position - 21*cm, 'XIN CẢM ƠN QUÝ KHÁCH')
    except Exception as e:
        # More descriptive error handling
        print(f"QR code error: {str(e)}")
        # If QR code insertion fails, still draw the thank you message
        set_font('normal', 36)
        c.drawCentredString(width/2, y_position - 4*cm, 'XIN CẢM ƠN QUÝ KHÁCH')# Lấy thông tin giảm giá (nếu có)
    
    # Save the PDF
    c.save()
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data
    
def download_link(content, filename, text, is_pdf=False):
    """Generate a link to download content as a file"""
    if is_pdf:
        # For PDF content (bytes)
        b64 = base64.b64encode(content).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">{text}</a>'
    else:
        # For text content
        b64 = base64.b64encode(content.encode()).decode()
        href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{text}</a>'
    return href

# Function to delete a product
def delete_product(product_id):
    # Delete product from products DataFrame
    st.session_state.products = st.session_state.products[st.session_state.products['product_id'] != product_id]
    
    # Delete product's recipes from recipes DataFrame
    st.session_state.recipes = st.session_state.recipes[st.session_state.recipes['product_id'] != product_id]
    
    # Show success message
    st.success(f"Sản phẩm {product_id} đã được xóa thành công!")


def add_backup_restore_ui():
    """Add UI for backing up and restoring data"""
    st.subheader("Backup and Restore Data")
    
    backup_tab, restore_tab = st.tabs(["Backup", "Restore"])
    
    with backup_tab:
        st.write("Download your data to keep a backup:")
        
        # Individual file downloads
        st.write("##### Individual Files")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Products and recipes
            csv_products = st.session_state.products.to_csv(index=False)
            st.download_button(
                label="Download Products",
                data=csv_products,
                file_name="products.csv",
                mime="text/csv"
            )
            
            # Rest of download buttons...
        
        # Complete backup as JSON
        st.write("##### Complete Backup")
        all_data = {
            "products": st.session_state.products.to_dict(orient='records'),
            "materials": st.session_state.materials.to_dict(orient='records'),
            "recipes": st.session_state.recipes.to_dict(orient='records'),
            "orders": st.session_state.orders.to_dict(orient='records'),
            "order_items": st.session_state.order_items.to_dict(orient='records'),
            "invoices": st.session_state.invoices.to_dict(orient='records'),
            "invoice_status": st.session_state.invoice_status.to_dict(orient='records'),
            "income": st.session_state.income.to_dict(orient='records'),
            "material_costs": st.session_state.material_costs.to_dict(orient='records')
        }
        
        json_data = json.dumps(all_data, ensure_ascii=False, indent=2)
        st.download_button(
            label="Download Complete Backup (JSON)",
            data=json_data,
            file_name="bakery_complete_backup.json",
            mime="application/json"
        )
    
    with restore_tab:
        st.write("Restore your data from a backup file:")
        
        restore_type = st.radio(
            "Select restore type",
            ["Individual CSV files", "Complete JSON backup"]
        )
        
        if restore_type == "Individual CSV files":
            file_type = st.selectbox(
                "Select file type to restore",
                ["products", "materials", "recipes", "orders", "order_items", 
                "invoices", "income", "material_costs", "invoice_status"]
            )
            
            uploaded_file = st.file_uploader(f"Upload {file_type}.csv", type="csv")
            
            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file)
                    st.session_state[file_type] = df
                    
                    # Save to storage
                    save_dataframe(df, f"{file_type}.csv")
                    
                    st.success(f"Successfully restored {file_type} data with {len(df)} rows!")
                except Exception as e:
                    st.error(f"Error uploading file: {str(e)}")
        else:
            uploaded_json = st.file_uploader("Upload complete JSON backup", type="json")
            
            if uploaded_json is not None:
                try:
                    data = json.load(uploaded_json)
                    
                    for key, records in data.items():
                        if not records:
                            # Skip empty data
                            continue
                            
                        df = pd.DataFrame.from_records(records)
                        st.session_state[key] = df
                        
                        # Save to storage
                        save_dataframe(df, f"{key}.csv")
                    
                    st.success("Successfully restored all data from backup!")
                    st.info("Please reload the app to apply all changes.")
                except Exception as e:
                    st.error(f"Error uploading JSON backup: {str(e)}")

# Main app navigation
st.title("Hệ Thống Quản Lý Tiệm Bánh 🍰")

# Sidebar navigation
if 'sidebar_selection' not in st.session_state:
    st.session_state.sidebar_selection = "Quản lý Đơn hàng"
    
previous_selection = st.session_state.sidebar_selection
    
tab_selection = st.sidebar.radio(
    "Điều hướng",
    ["Quản lý Đơn hàng", "Theo dõi Doanh thu", "Kho Nguyên liệu", "Quản lý Sản phẩm", "Quản lý Hóa đơn", "Quản lý Dữ liệu"],
    index=["Quản lý Đơn hàng", "Theo dõi Doanh thu", "Kho Nguyên liệu", "Quản lý Sản phẩm", "Quản lý Hóa đơn", "Quản lý Dữ liệu"].index(st.session_state.sidebar_selection)
)

# Cập nhật sidebar_selection và tự động rerun nếu giá trị thay đổi
if previous_selection != tab_selection:
    st.session_state.sidebar_selection = tab_selection
    st.rerun()

# Order Management Tab
if tab_selection == "Quản lý Đơn hàng":
    st.header("Quản lý Đơn hàng")
    
    order_tab1, order_tab2 = st.tabs(["Đơn hàng Mới", "Lịch sử Đơn hàng"])
    
    with order_tab1:
        st.subheader("Tạo Đơn hàng Mới")
        
        col1, col2 = st.columns(2)
        with col1:
            customer_name = st.text_input("Tên Khách hàng")
            customer_phone = st.text_input("Số điện thoại")
        with col2:
            customer_address = st.text_area("Địa chỉ giao hàng", height=100)
        
        # Product selection
        st.subheader("Lựa chọn Sản phẩm")
        
        # Kiểm tra xem có sản phẩm nào không
        if st.session_state.products.empty:
            st.warning("Chưa có sản phẩm nào trong hệ thống. Vui lòng tạo sản phẩm trước trong mục 'Quản lý Sản phẩm'.")
            
            # Thêm nút dẫn đến phần quản lý sản phẩm
            if st.button("Đi đến Quản lý Sản phẩm"):
                st.session_state.sidebar_selection = "Quản lý Sản phẩm"
                st.rerun()  # Sửa từ st.rerun() thành st.experimental_rerun()
                
            # Không hiển thị phần còn lại của đơn hàng khi không có sản phẩm
            st.stop()
        else:
            # Display available products with quantity selection
            selected_products = []
            quantities = []
            
            cols = st.columns(4)
            for i, (_, product) in enumerate(st.session_state.products.iterrows()):
                with cols[i % 4]:
                    st.write(f"**{product['name']}**")
                    st.write(f"{product['price']:,.0f} VND")
                    quantity = st.number_input(f"SL {product['name']}", min_value=0, value=0, key=f"qty_{product['product_id']}")
                    if quantity > 0:
                        selected_products.append(product)
                        quantities.append(quantity)
                    st.write("---")
        
        # Calculate total product amount
        total_product_amount = sum(p['price'] * q for p, q in zip(selected_products, quantities))
        
        # Shipping fee input
        st.subheader("Phí vận chuyển")
        shipping_fee = st.number_input("Phí vận chuyển (VND)", min_value=0, value=0, step=1000)
        
        # Mã giảm giá
        st.subheader("Mã giảm giá")
        discount_code = st.text_input("Nhập mã giảm giá (nếu có)")
        discount_amount = 0
        discount_rate = 0

        # Kiểm tra và áp dụng mã giảm giá
        if discount_code:
            discount_amount, discount_rate = apply_discount_code(discount_code, total_product_amount)
            if discount_amount > 0:
                st.success(f"Mã giảm giá hợp lệ! Bạn được giảm {discount_rate*100:.0f}% ({discount_amount:,.0f} VND)")
            else:
                st.error("Mã giảm giá không hợp lệ hoặc đã hết hạn")

        # Tính tổng tiền sau khi áp dụng giảm giá
        discounted_product_amount = total_product_amount - discount_amount

        # Tính tổng cộng (sản phẩm sau giảm giá + phí vận chuyển)
        total_amount = discounted_product_amount + shipping_fee
                
        # Display totals
        # Thay thế phần hiển thị tổng tiền hiện tại bằng code sau
        st.subheader("Tổng tiền")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.write(f"**Tổng sản phẩm:** {total_product_amount:,.0f} VND")
        with col2:
            if discount_amount > 0:
                st.write(f"**Giảm giá ({discount_rate*100:.0f}%):** -{discount_amount:,.0f} VND")
            else:
                st.write("**Giảm giá:** 0 VND")
        with col3:
            st.write(f"**Phí vận chuyển:** {shipping_fee:,.0f} VND")
        with col4:
            st.write(f"**Tổng cộng:** {total_amount:,.0f} VND")
        
        if st.button("Tạo Đơn hàng", key="create_order"):
            if not customer_name:
                st.error("Vui lòng nhập tên khách hàng")
            elif len(selected_products) == 0:
                st.error("Vui lòng chọn ít nhất một sản phẩm")
            else:
                # Kiểm tra xem có đủ nguyên liệu không
                sufficient, insufficient_materials = check_sufficient_materials(selected_products, quantities)
                
                if not sufficient:
                    # Hiển thị thông báo thiếu nguyên liệu
                    st.error("Không đủ nguyên liệu để thực hiện đơn hàng này!")
                    
                    # Hiển thị chi tiết các nguyên liệu thiếu
                    st.subheader("Nguyên liệu không đủ:")
                    
                    for material in insufficient_materials:
                        st.warning(f"**{material['name']}**: " +
                                f"Cần {material['required']:.5f} {material['unit']}, " +
                                f"có sẵn {material['available']:.5f} {material['unit']}, " +
                                f"thiếu {material['shortage']:.5f} {material['unit']}")
                    
                    # Gợi ý nhập thêm nguyên liệu
                    st.info("Vui lòng nhập thêm nguyên liệu vào kho trước khi tạo đơn hàng này.")
                    
                    # Tạo nút điều hướng đến tab nhập nguyên liệu
                    if st.button("Đi đến Nhập Nguyên liệu"):
                        st.session_state.sidebar_selection = "Kho Nguyên liệu"
                        st.rerun()
                else:
                    # Generate order ID
                    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
                    
                    # Create order
                    # Thêm thông tin giảm giá vào DataFrame đơn hàng khi tạo đơn hàng mới
                    new_order = pd.DataFrame({
                        'order_id': [order_id],
                        'date': [date.today().strftime("%Y-%m-%d")],
                        'customer_name': [customer_name],
                        'customer_phone': [customer_phone],
                        'customer_address': [customer_address],
                        'total_amount': [discounted_product_amount],  # Giá trị sản phẩm sau khi giảm giá
                        'shipping_fee': [shipping_fee],  # Phí vận chuyển
                        'discount_code': [discount_code if discount_amount > 0 else ''],  # Lưu mã giảm giá
                        'discount_amount': [discount_amount],  # Lưu số tiền giảm giá
                        'status': ['Hoàn thành']
                    })
                    
                    # Create order items
                    new_order_items = []
                    for product, quantity in zip(selected_products, quantities):
                        new_order_items.append({
                            'order_id': order_id,
                            'product_id': product['product_id'],
                            'quantity': quantity,
                            'price': product['price'],
                            'subtotal': product['price'] * quantity
                        })
                    
                    new_order_items_df = pd.DataFrame(new_order_items)
                    
                    # Update session state
                    st.session_state.orders = pd.concat([st.session_state.orders, new_order], ignore_index=True)
                    st.session_state.order_items = pd.concat([st.session_state.order_items, new_order_items_df], ignore_index=True)
                    
                    # Update materials inventory - đảm bảo đủ nguyên liệu
                    update_success = update_materials_after_order(order_id)
                    
                    if update_success:
                        # Update income records
                        update_income(order_id)
                        
                        # Create invoice
                        invoice_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
                        new_invoice = pd.DataFrame({
                            'invoice_id': [invoice_id],
                            'order_id': [order_id],
                            'date': [date.today().strftime("%Y-%m-%d")],
                            'customer_name': [customer_name],
                            'total_amount': [total_amount],  # Use grand total (products + shipping)
                            'payment_method': ['Tiền mặt']  # Default payment method
                        })
                        
                        st.session_state.invoices = pd.concat([st.session_state.invoices, new_invoice], ignore_index=True)
                        
                        st.success(f"Đơn hàng {order_id} đã được tạo thành công!")
                        
                        # Generate invoice download link
                        pdf_data = generate_invoice_content(invoice_id, order_id, as_pdf=True)
                        st.markdown(download_link(pdf_data, f"Hoadon_{invoice_id}.pdf", "Tải Hóa đơn (PDF)", is_pdf=True), unsafe_allow_html=True)

                        # Save data after creating order
                        save_dataframe(st.session_state.orders, "orders.csv")
                        save_dataframe(st.session_state.order_items, "order_items.csv")
                        save_dataframe(st.session_state.invoices, "invoices.csv")
                        save_dataframe(st.session_state.materials, "materials.csv")
                        save_dataframe(st.session_state.income, "income.csv")
                    else:
                        # Xóa đơn hàng nếu việc cập nhật nguyên liệu thất bại
                        st.session_state.orders = st.session_state.orders[st.session_state.orders['order_id'] != order_id]
                        st.session_state.order_items = st.session_state.order_items[st.session_state.order_items['order_id'] != order_id]
                        st.error("Không thể tạo đơn hàng do lỗi khi cập nhật nguyên liệu!")
    
    with order_tab2:
        st.subheader("Lịch sử Đơn hàng")
        
        if len(st.session_state.orders) > 0:
            st.dataframe(st.session_state.orders.sort_values('date', ascending=False))
            
            # Order details view
            selected_order_id = st.selectbox("Chọn Đơn hàng để Xem Chi tiết", 
                                           options=st.session_state.orders['order_id'].tolist(),
                                           format_func=lambda x: f"{x} - {st.session_state.orders[st.session_state.orders['order_id'] == x]['customer_name'].iloc[0]}")
            
            if selected_order_id:
                st.write("### Chi tiết Đơn hàng")
                order_details = st.session_state.order_items[st.session_state.order_items['order_id'] == selected_order_id]
                
                # Get product names
                order_details = order_details.merge(
                    st.session_state.products[['product_id', 'name']],
                    on='product_id',
                    how='left'
                )
                
                st.dataframe(order_details[['name', 'quantity', 'price', 'subtotal']])
        else:
            st.info("Chưa có đơn hàng nào. Hãy tạo đơn hàng mới để xem ở đây.")

# Income Tracking Tab - Updated with Revenue and Cost Table
elif tab_selection == "Theo dõi Doanh thu":
    st.header("Theo dõi Doanh thu")
    
    # Initialize material import cost tracking if not exists
    if 'material_costs' not in st.session_state:
        st.session_state.material_costs = pd.DataFrame(columns=[
            'date', 'material_id', 'quantity', 'total_cost', 'supplier'
        ])

    if 'marketing_costs' not in st.session_state:
        st.session_state.marketing_costs = pd.DataFrame(columns=[
            'date', 'campaign_name', 'description', 'platform', 'amount', 'notes'
        ])
    
    income_tab1, income_tab2, income_tab3, income_tab4 = st.tabs([
            "Báo cáo Tổng quan", "Chi phí Nguyên liệu", "Chi phí Nhân công", "Chi phí Marketing"
        ])    
    # Helper function to create monthly summary
    # Cập nhật hàm create_monthly_summary để phản ánh đúng cấu trúc chi phí mới

    def create_monthly_summary(income_df, material_costs_df, labor_costs_df, start_date, end_date):
        """Tạo bảng tổng hợp doanh thu và chi phí theo tháng"""
        # Ensure we have data in the correct format
        if income_df.empty and material_costs_df.empty and labor_costs_df.empty:
            return pd.DataFrame()
            
        # Convert date strings to datetime objects for proper handling
        income_df['date_obj'] = pd.to_datetime(income_df['date'])
        if not material_costs_df.empty:
            material_costs_df['date_obj'] = pd.to_datetime(material_costs_df['date'])
        if not labor_costs_df.empty:
            labor_costs_df['date_obj'] = pd.to_datetime(labor_costs_df['date'])
        
        # Create a date range from start to end
        date_range = pd.date_range(start=start_date, end=end_date, freq='MS')  # MS = Month Start
        
        # Prepare results table
        results = []
        
        for date in date_range:
            month_name = date.strftime('%m/%Y')
            month_start = date.strftime('%Y-%m-%d')
            month_end = (date + pd.offsets.MonthEnd(1)).strftime('%Y-%m-%d')
            
            # Filter income data for this month
            month_income = income_df[(income_df['date_obj'] >= month_start) & 
                                (income_df['date_obj'] <= month_end)]
            
            # Calculate income values
            total_sales = month_income['total_sales'].sum() if not month_income.empty else 0
            cost_of_goods = month_income['cost_of_goods'].sum() if not month_income.empty else 0
            
            # Lấy chi phí khác từ income data
            other_costs = 0
            if 'other_costs' in month_income.columns:
                other_costs = month_income['other_costs'].sum() if not month_income.empty else 0
            
            # Lấy chi phí khấu hao từ income data
            depreciation_costs = 0
            if 'depreciation_costs' in month_income.columns:
                depreciation_costs = month_income['depreciation_costs'].sum() if not month_income.empty else 0
                
            # Lấy chi phí giảm giá từ income data - THÊM MỚI
            discount_costs = 0
            if 'discount_costs' in month_income.columns:
                discount_costs = month_income['discount_costs'].sum() if not month_income.empty else 0
            
            # Calculate material costs for this month (chi phí nhập hàng)
            material_costs = 0
            if not material_costs_df.empty:
                month_costs = material_costs_df[(material_costs_df['date_obj'] >= month_start) & 
                                            (material_costs_df['date_obj'] <= month_end)]
                material_costs = month_costs['total_cost'].sum() if not month_costs.empty else 0
            
            # Calculate labor costs for this month (chi phí nhân công)
            labor_costs = 0
            if not labor_costs_df.empty:
                month_labor = labor_costs_df[(labor_costs_df['date_obj'] >= month_start) & 
                                        (labor_costs_df['date_obj'] <= month_end)]
                labor_costs = month_labor['total_cost'].sum() if not month_labor.empty else 0
            
            # Tính tổng chi phí từ tất cả các thành phần (bao gồm cả chi phí giảm giá) - THÊM MỚI
            total_cost = other_costs + depreciation_costs + material_costs + labor_costs + discount_costs
            
            # Tính lợi nhuận ròng
            net_profit = total_sales - total_cost
            
            # Calculate profit margin
            profit_margin = (net_profit / total_sales * 100) if total_sales > 0 else 0
            
            # Tạo dòng kết quả cho tháng này (bao gồm chi phí giảm giá) - THÊM MỚI
            results.append({
                'Tháng': month_name,
                'Doanh thu': total_sales,
                'Chi phí Nguyên liệu đã sử dụng': cost_of_goods,
                'Chi phí Nhập hàng': material_costs,
                'Chi phí Nhân công': labor_costs,
                'Chi phí Khác': other_costs,
                'Chi phí Khấu hao': depreciation_costs,
                'Chi phí Giảm giá': discount_costs,  # THÊM MỚI
                'Tổng Chi phí': total_cost,
                'Lợi nhuận': net_profit,
                'Tỷ suất': profit_margin
            })
        
        return pd.DataFrame(results)
    
    # Define a function to handle date range changes
    def handle_date_change():
        if "date_selected" in st.session_state:
            # Force a rerun by updating another session state variable
            st.session_state.date_changed = True

   # Cập nhật hiển thị báo cáo doanh thu với tất cả các tính năng trong một tab
    with income_tab1:
            if len(st.session_state.income) > 0:
                # Sort by date
                income_df = st.session_state.income.sort_values('date', ascending=False)
                material_costs_df = st.session_state.material_costs.copy() if 'material_costs' in st.session_state else pd.DataFrame()
                labor_costs_df = st.session_state.labor_costs.copy() if 'labor_costs' in st.session_state else pd.DataFrame()
                marketing_costs_df = st.session_state.marketing_costs.copy() if 'marketing_costs' in st.session_state else pd.DataFrame()
                
                # Date filter - Handle date range safely
                try:
                    # Get min and max dates from data
                    min_date_str = income_df['date'].min()
                    max_date_str = income_df['date'].max()
                    
                    min_date = datetime.datetime.strptime(min_date_str, '%Y-%m-%d').date()
                    max_date = datetime.datetime.strptime(max_date_str, '%Y-%m-%d').date()
                    
                    # Ensure that min_date and max_date are valid and equal if there's only one date
                    if min_date > max_date:
                        min_date, max_date = max_date, min_date
                        
                    # Use today's date if within range, otherwise use max_date
                    today = datetime.date.today()
                    
                    # Set default_end (making sure it's within valid range)
                    if today < min_date:
                        default_end = min_date
                    elif today > max_date:
                        default_end = max_date
                    else:
                        default_end = today
                    
                    # Set default_start (making sure it's within valid range)
                    first_day_of_month = datetime.date(today.year, today.month, 1)
                    if first_day_of_month < min_date:
                        default_start = min_date
                    elif first_day_of_month > max_date:
                        default_start = max_date
                    else:
                        default_start = first_day_of_month
                    
                    # Ensure the default range is valid
                    if default_start > default_end:
                        default_start = default_end
                    
                    # Initialize date range in session state if not present
                    if 'income_date_start' not in st.session_state or 'income_date_end' not in st.session_state:
                        st.session_state.income_date_start = default_start
                        st.session_state.income_date_end = default_end
                    
                    # Ensure session state dates are within min_date and max_date
                    if st.session_state.income_date_start < min_date:
                        st.session_state.income_date_start = min_date
                    elif st.session_state.income_date_start > max_date:
                        st.session_state.income_date_start = max_date
                        
                    if st.session_state.income_date_end < min_date:
                        st.session_state.income_date_end = min_date
                    elif st.session_state.income_date_end > max_date:
                        st.session_state.income_date_end = max_date
                    
                    # Create date range input
                    col1, col2 = st.columns(2)
                    with col1:
                        start_date = st.date_input(
                            "Từ ngày",
                            value=st.session_state.income_date_start,
                            min_value=min_date,
                            max_value=max_date,
                            key="income_date_start_input"
                        )
                    
                    with col2:
                        end_date = st.date_input(
                            "Đến ngày",
                            value=st.session_state.income_date_end,
                            min_value=min_date,
                            max_value=max_date,
                            key="income_date_end_input"
                        )
                    
                    # Update session state with selected dates
                    st.session_state.income_date_start = start_date
                    st.session_state.income_date_end = end_date
                    
                    # Convert dates to string format for filtering
                    start_date_str = start_date.strftime('%Y-%m-%d')
                    end_date_str = end_date.strftime('%Y-%m-%d')
                    
                    # Apply filter button
                    if st.button("Áp dụng lọc", key="apply_filter_btn"):
                        # This button exists just to trigger a rerun with the new dates
                        pass
                        
                    # Filter income data
                    filtered_income = income_df[
                        (income_df['date'] >= start_date_str) & 
                        (income_df['date'] <= end_date_str)
                    ]
                    
                    # Check if we have data in the selected range
                    if filtered_income.empty:
                        st.info(f"Không có dữ liệu doanh thu trong khoảng từ {start_date_str} đến {end_date_str}.")
                    else:
                        # Filter material costs data (chi phí nhập hàng)
                        filtered_costs = pd.DataFrame()
                        material_costs_in_period = 0
                        if not material_costs_df.empty:
                            filtered_costs = material_costs_df[
                                (material_costs_df['date'] >= start_date_str) & 
                                (material_costs_df['date'] <= end_date_str)
                            ]
                            material_costs_in_period = filtered_costs['total_cost'].sum() if not filtered_costs.empty else 0
                        
                        # Filter labor costs data (chi phí nhân công)
                        filtered_labor = pd.DataFrame()
                        labor_costs_in_period = 0
                        if not labor_costs_df.empty:
                            filtered_labor = labor_costs_df[
                                (labor_costs_df['date'] >= start_date_str) & 
                                (labor_costs_df['date'] <= end_date_str)
                            ]
                            labor_costs_in_period = filtered_labor['total_cost'].sum() if not filtered_labor.empty else 0
                        
                        # Filter marketing costs data (chi phí marketing)
                        filtered_marketing = pd.DataFrame()
                        marketing_costs = 0
                        if not marketing_costs_df.empty:
                            filtered_marketing = marketing_costs_df[
                                (marketing_costs_df['date'] >= start_date_str) & 
                                (marketing_costs_df['date'] <= end_date_str)
                            ]
                            marketing_costs = filtered_marketing['amount'].sum() if not filtered_marketing.empty else 0

                        # Get other costs from income data
                        other_production_costs = 0
                        if 'other_costs' in filtered_income.columns:
                            other_production_costs = filtered_income['other_costs'].sum()
                        
                        # Get depreciation costs
                        depreciation_costs = 0
                        if 'depreciation_costs' in filtered_income.columns:
                            depreciation_costs = filtered_income['depreciation_costs'].sum()

                        # Get discount costs 
                        discount_costs = 0
                        if 'discount_costs' in filtered_income.columns:
                            discount_costs = filtered_income['discount_costs'].sum()
                        
                        # Calculate total profit with all costs considered
                        total_sales = filtered_income['total_sales'].sum()
                        cost_of_goods = filtered_income['cost_of_goods'].sum()
                        total_profit = filtered_income['profit'].sum()
                        
                        # Calculate total costs
                        total_costs = (
                            cost_of_goods + 
                            material_costs_in_period + 
                            labor_costs_in_period + 
                            other_production_costs + 
                            depreciation_costs + 
                            discount_costs + 
                            marketing_costs
                        )
                        
                        # Calculate net profit
                        net_profit = total_sales - total_costs
                        
                        # Display income summary
                        st.subheader("Tổng quan Doanh thu")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Tổng Doanh thu", f"{total_sales:,.0f} VND")
                        with col2:
                            st.metric("Tổng Chi phí", f"{total_costs:,.0f} VND")
                        with col3:
                            st.metric("Lợi nhuận Ròng", f"{net_profit:,.0f} VND")
                        
                        # Set a smaller font size for metric values
                        st.markdown("""
                        <style>
                            .stMetric .css-1wivap2 {
                                font-size: 1.0rem !important;
                                overflow: visible !important;
                                text-overflow: clip !important;
                                white-space: normal !important;
                            }
                        </style>
                        """, unsafe_allow_html=True)
                        
                        # Display detailed costs
                        st.subheader("Chi tiết Chi phí")
                        
                        # First row of detailed costs
                        row2_col1, row2_col2, row2_col3 = st.columns(3)
                        
                        with row2_col1:
                            st.metric(
                                "Chi phí Nguyên liệu đã sử dụng", 
                                f"{cost_of_goods:,.0f} VND",
                                delta=None
                            )
                        
                        with row2_col2:
                            st.metric(
                                "Chi phí Nhập hàng", 
                                f"{material_costs_in_period:,.0f} VND",
                                delta=None
                            )
                        
                        with row2_col3:
                            st.metric(
                                "Chi phí Nhân công", 
                                f"{labor_costs_in_period:,.0f} VND",
                                delta=None
                            )
                        
                        # Second row of detailed costs
                        row3_col1, row3_col2, row3_col3 = st.columns(3)
                        
                        with row3_col1:
                            st.metric(
                                "Chi phí Khác", 
                                f"{other_production_costs:,.0f} VND",
                                delta=None
                            )
                        
                        with row3_col2:
                            st.metric(
                                "Chi phí Khấu hao", 
                                f"{depreciation_costs:,.0f} VND",
                                delta=None
                            )
                        
                        with row3_col3:
                            st.metric(
                                "Chi phí Giảm giá", 
                                f"{discount_costs:,.0f} VND",
                                delta=None
                            )
                        
                        # Third row for marketing costs
                        row4_col1, row4_col2, row4_col3 = st.columns(3)
                        
                        with row4_col1:
                            st.metric(
                                "Chi phí Marketing", 
                                f"{marketing_costs:,.0f} VND",
                                delta=None
                            )
                        
                        # Display profit margins
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("#### Chi tiết Chi phí:")
                            st.write(f"- Chi phí Nguyên liệu đã sử dụng: **{cost_of_goods:,.0f} VND**")
                            st.write(f"- Chi phí Nhân công: **{labor_costs_in_period:,.0f} VND**")
                            st.write(f"- Chi phí Khác: **{other_production_costs:,.0f} VND**")
                            st.write(f"- Chi phí Khấu hao: **{depreciation_costs:,.0f} VND**")
                            st.write(f"- Chi phí Nhập hàng: **{material_costs_in_period:,.0f} VND**")
                            st.write(f"- Chi phí Giảm giá: **{discount_costs:,.0f} VND**")
                            st.write(f"- Chi phí Marketing: **{marketing_costs:,.0f} VND**")
                            st.write(f"- **Tổng Chi phí: {total_costs:,.0f} VND**")
                        
                        with col2:
                            # Display profit margins
                            if total_sales > 0:
                                gross_margin = (total_profit / total_sales) * 100
                                net_margin = (net_profit / total_sales) * 100
                                
                                st.write("#### Tỷ suất Lợi nhuận:")
                                st.write(f"- Tỷ suất Lợi nhuận Gộp: **{gross_margin:.2f}%**")
                                st.write(f"- Tỷ suất Lợi nhuận Ròng: **{net_margin:.2f}%**")
                        
                        # Create biểu đồ using the same data as above
                        st.subheader("Biểu đồ Doanh thu")
                        
                        # Create data for chart
                        chart_data = {
                            "Loại": [],
                            "Giá trị": []
                        }
                        
                        # Add data points
                        chart_data["Loại"].append("Doanh thu")
                        chart_data["Giá trị"].append(total_sales)
                        
                        chart_data["Loại"].append("Chi phí Nguyên liệu")
                        chart_data["Giá trị"].append(cost_of_goods)
                        
                        chart_data["Loại"].append("Chi phí Nhập hàng")
                        chart_data["Giá trị"].append(material_costs_in_period)
                        
                        chart_data["Loại"].append("Chi phí Nhân công")
                        chart_data["Giá trị"].append(labor_costs_in_period)
                        
                        chart_data["Loại"].append("Chi phí Khác")
                        chart_data["Giá trị"].append(other_production_costs)
                        
                        chart_data["Loại"].append("Chi phí Khấu hao")
                        chart_data["Giá trị"].append(depreciation_costs)
                        
                        chart_data["Loại"].append("Chi phí Giảm giá")
                        chart_data["Giá trị"].append(discount_costs)
                        
                        chart_data["Loại"].append("Chi phí Marketing")
                        chart_data["Giá trị"].append(marketing_costs)
                        
                        chart_data["Loại"].append("Tổng Chi phí")
                        chart_data["Giá trị"].append(total_costs)
                        
                        chart_data["Loại"].append("Lợi nhuận Ròng")
                        chart_data["Giá trị"].append(net_profit)
                        
                        # Convert to DataFrame
                        chart_df = pd.DataFrame(chart_data)
                        
                        # Initialize chart type in session state if not present
                        if 'chart_type' not in st.session_state:
                            st.session_state.chart_type = "Cột"
                        
                        # Chart type selection
                        chart_type = st.radio(
                            "Loại biểu đồ",
                            ["Cột", "Đường"],
                            horizontal=True,
                            index=0 if st.session_state.chart_type == "Cột" else (1 if st.session_state.chart_type == "Đường" else 2),
                            key="chart_type_radio"
                        )
                        
                        # Update session state
                        st.session_state.chart_type = chart_type
                        
                        # Available metrics - use the actual data from above
                        available_metrics = [
                            "Doanh thu", 
                            "Chi phí Nguyên liệu", 
                            "Chi phí Nhập hàng", 
                            "Chi phí Nhân công", 
                            "Chi phí Khác",
                            "Chi phí Khấu hao",
                            "Chi phí Giảm giá",
                            "Chi phí Marketing",
                            "Tổng Chi phí", 
                            "Lợi nhuận Ròng"
                        ]
                        
                        # Initialize metrics in session state if not present
                        if 'selected_metrics' not in st.session_state:
                            st.session_state.selected_metrics = ["Doanh thu", "Tổng Chi phí", "Lợi nhuận Ròng"]
                        
                        # Metrics selection
                        selected_metrics = st.multiselect(
                            "Chọn các chỉ số để hiển thị",
                            available_metrics,
                            default=st.session_state.selected_metrics,
                            key="metrics_multiselect"
                        )
                        
                        # Update session state
                        st.session_state.selected_metrics = selected_metrics
                        
                        # Filter chart data based on selected metrics
                        if selected_metrics:
                            filtered_chart_df = chart_df[chart_df["Loại"].isin(selected_metrics)]
                            
                            # Define a consistent color palette (add more colors if needed)
                            colors = {
                                "Doanh thu": "#4CAF50",  # Green
                                "Chi phí Nguyên liệu": "#F44336",  # Red
                                "Chi phí Nhập hàng": "#FF5722",  # Deep Orange
                                "Chi phí Nhân công": "#9C27B0",  # Purple
                                "Chi phí Khác": "#3F51B5",  # Indigo
                                "Chi phí Khấu hao": "#03A9F4",  # Light Blue
                                "Chi phí Giảm giá": "#009688",  # Teal
                                "Chi phí Marketing": "#FFC107",  # Amber
                                "Tổng Chi phí": "#795548",  # Brown
                                "Lợi nhuận Ròng": "#2196F3"  # Blue
                            }
                            
                            # Create chart based on chart type
                            if chart_type == "Cột":
                                # Create bar chart using Plotly
                                fig = go.Figure()
                                
                                for metric in selected_metrics:
                                    value = filtered_chart_df[filtered_chart_df["Loại"] == metric]["Giá trị"].values[0]
                                    fig.add_trace(go.Bar(
                                        x=[metric],
                                        y=[value],
                                        name=metric,
                                        marker_color=colors.get(metric, "#000000")
                                    ))
                                
                                # Update layout
                                fig.update_layout(
                                    title="Biểu đồ Doanh thu và Chi phí",
                                    xaxis_title="Loại",
                                    yaxis_title="Giá trị (VND)",
                                    legend_title="Chỉ số",
                                    bargap=0.3,
                                    height=500
                                )
                                
                                # Format y-axis to use comma separation for thousands
                                fig.update_yaxes(tickformat=",")
                                
                                # Display the chart
                                st.plotly_chart(fig, use_container_width=True)
                                
                            elif chart_type == "Đường":
                                # For line chart, we need to handle differently as each metric is a single point
                                # We'll create a dummy x-axis with evenly spaced points
                                
                                # Create line chart using Plotly
                                fig = go.Figure()
                                
                                for i, metric in enumerate(selected_metrics):
                                    value = filtered_chart_df[filtered_chart_df["Loại"] == metric]["Giá trị"].values[0]
                                    
                                    # Add line
                                    fig.add_trace(go.Scatter(
                                        x=[i],
                                        y=[value],
                                        mode='lines+markers',
                                        name=metric,
                                        line=dict(color=colors.get(metric, "#000000"), width=3),
                                        marker=dict(color=colors.get(metric, "#000000"), size=10)
                                    ))
                                
                                # Update layout
                                fig.update_layout(
                                    title="Biểu đồ Doanh thu và Chi phí",
                                    xaxis_title="Loại",
                                    yaxis_title="Giá trị (VND)",
                                    legend_title="Chỉ số",
                                    height=500
                                )
                                
                                # Set x-axis to use the metric names instead of numbers
                                fig.update_xaxes(
                                    tickmode='array',
                                    tickvals=list(range(len(selected_metrics))),
                                    ticktext=selected_metrics
                                )
                                
                                # Format y-axis to use comma separation for thousands
                                fig.update_yaxes(tickformat=",")
                                
                                # Display the chart
                                st.plotly_chart(fig, use_container_width=True)
                            
                            # Add a downloadable CSV option for the filtered chart data
                            st.download_button(
                                label="Tải dữ liệu xuống (CSV)",
                                data=filtered_chart_df.to_csv(index=False).encode('utf-8'),
                                file_name=f'bao_cao_doanh_thu_{start_date_str}_den_{end_date_str}.csv',
                                mime='text/csv',
                            )
                            
                            # Add a section to show the data table
                            with st.expander("Xem bảng dữ liệu"):
                                # Format the values in the DataFrame for display
                                display_df = filtered_chart_df.copy()
                                display_df['Giá trị'] = display_df['Giá trị'].apply(lambda x: f"{x:,.0f} VND")
                                st.dataframe(display_df)
                            
                            # Add a pie chart visualization option
                            if st.checkbox("Hiển thị dạng biểu đồ tròn", key="show_pie_chart"):
                                st.subheader("Biểu đồ tròn Chi phí")
                                
                                # Create a filtered dataframe for costs only (excluding revenue and profit)
                                cost_categories = [metric for metric in selected_metrics if "Chi phí" in metric]
                                
                                if cost_categories:
                                    cost_df = filtered_chart_df[filtered_chart_df["Loại"].isin(cost_categories)]
                                    
                                    # Create a pie chart for costs
                                    fig = go.Figure(data=[go.Pie(
                                        labels=cost_df["Loại"],
                                        values=cost_df["Giá trị"],
                                        hole=.3,
                                        marker_colors=[colors.get(metric, "#000000") for metric in cost_df["Loại"]]
                                    )])
                                    
                                    fig.update_layout(
                                        title="Cơ cấu Chi phí",
                                        height=500
                                    )
                                    
                                    # Add percentage and value to hover information
                                    fig.update_traces(
                                        hoverinfo='label+percent+value',
                                        textinfo='percent',
                                        textfont_size=14
                                    )
                                    
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.info("Vui lòng chọn ít nhất một loại chi phí để hiển thị biểu đồ tròn.")
                            
                            # Add a time series analysis section if there are multiple dates in the data
                            if len(filtered_income['date'].unique()) > 1 and st.checkbox("Phân tích theo thời gian", key="show_time_analysis"):
                                st.subheader("Phân tích doanh thu theo thời gian")
                                
                                # Group data by date
                                time_df = filtered_income.groupby('date').agg({
                                    'total_sales': 'sum',
                                    'cost_of_goods': 'sum',
                                    'profit': 'sum'
                                }).reset_index()
                                
                                # Sort by date
                                time_df = time_df.sort_values('date')
                                
                                # Create time series chart
                                fig = go.Figure()
                                
                                # Add traces
                                fig.add_trace(go.Scatter(
                                    x=time_df['date'],
                                    y=time_df['total_sales'],
                                    mode='lines+markers',
                                    name='Doanh thu',
                                    line=dict(color=colors.get('Doanh thu', "#4CAF50"), width=3)
                                ))
                                
                                fig.add_trace(go.Scatter(
                                    x=time_df['date'],
                                    y=time_df['cost_of_goods'],
                                    mode='lines+markers',
                                    name='Chi phí Nguyên liệu',
                                    line=dict(color=colors.get('Chi phí Nguyên liệu', "#F44336"), width=3)
                                ))
                                
                                fig.add_trace(go.Scatter(
                                    x=time_df['date'],
                                    y=time_df['profit'],
                                    mode='lines+markers',
                                    name='Lợi nhuận',
                                    line=dict(color=colors.get('Lợi nhuận Ròng', "#2196F3"), width=3)
                                ))
                                
                                # Update layout
                                fig.update_layout(
                                    title='Doanh thu, Chi phí và Lợi nhuận theo thời gian',
                                    xaxis_title='Ngày',
                                    yaxis_title='Giá trị (VND)',
                                    height=500,
                                    legend_title="Chỉ số"
                                )
                                
                                # Format y-axis to use comma separation for thousands
                                fig.update_yaxes(tickformat=",")
                                
                                # Display the chart
                                st.plotly_chart(fig, use_container_width=True)
                                
                                # Add a trend analysis if enough data points
                                if len(time_df) >= 5:
                                    st.subheader("Phân tích xu hướng")
                                    
                                    # Add a column for moving average of revenue
                                    time_df['total_sales_ma3'] = time_df['total_sales'].rolling(window=3, min_periods=1).mean()
                                    
                                    # Create a trend analysis chart
                                    fig = go.Figure()
                                    
                                    # Add raw data
                                    fig.add_trace(go.Scatter(
                                        x=time_df['date'],
                                        y=time_df['total_sales'],
                                        mode='lines+markers',
                                        name='Doanh thu thực tế',
                                        line=dict(color="#4CAF50", width=2)
                                    ))
                                    
                                    # Add moving average
                                    fig.add_trace(go.Scatter(
                                        x=time_df['date'],
                                        y=time_df['total_sales_ma3'],
                                        mode='lines',
                                        name='Trung bình động 3 ngày',
                                        line=dict(color="#FF9800", width=3, dash='dash')
                                    ))
                                    
                                    # Update layout
                                    fig.update_layout(
                                        title='Phân tích xu hướng Doanh thu',
                                        xaxis_title='Ngày',
                                        yaxis_title='Doanh thu (VND)',
                                        height=400,
                                        legend_title="Dữ liệu"
                                    )
                                    
                                    # Format y-axis to use comma separation for thousands
                                    fig.update_yaxes(tickformat=",")
                                    
                                    # Display the chart
                                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    # Fallback if date parsing fails
                    st.error(f"Lỗi khi xử lý dữ liệu: {str(e)}")
                    st.info("Vui lòng kiểm tra dữ liệu doanh thu và chi phí.")
            else:
                st.info("Chưa có dữ liệu doanh thu. Hoàn thành đơn hàng để xem thông tin doanh thu.")

    
    with income_tab2:
        st.subheader("Chi phí nhập Nguyên liệu")
        
        if len(st.session_state.material_costs) > 0:
            # Display material costs
            material_costs_df = st.session_state.material_costs.copy()
            
            # Format material costs for display
            material_costs_display = pd.DataFrame({
                'Ngày': material_costs_df['date'],
                'Mã Nguyên liệu': material_costs_df['material_id'],
                'Số lượng': material_costs_df['quantity'],
                'Chi phí': material_costs_df['total_cost'].apply(lambda x: f"{x:,.0f} VND"),
                'Nhà cung cấp': material_costs_df['supplier']
            })
            
            # Date filter for material costs - with safer handling
            try:
                # Get min and max dates from data
                min_cost_date_str = material_costs_df['date'].min()
                max_cost_date_str = material_costs_df['date'].max()
                
                min_cost_date = datetime.datetime.strptime(min_cost_date_str, '%Y-%m-%d').date()
                max_cost_date = datetime.datetime.strptime(max_cost_date_str, '%Y-%m-%d').date()
                
                # Use today's date if within range, otherwise use max_date
                today = datetime.date.today()
                if today < min_cost_date:
                    default_end = min_cost_date
                elif today > max_cost_date:
                    default_end = max_cost_date
                else:
                    default_end = today
                
                # Use first day of current month or min_date, whichever is later
                first_day_of_month = datetime.date(today.year, today.month, 1)
                if first_day_of_month < min_cost_date:
                    default_start = min_cost_date
                elif first_day_of_month > max_cost_date:
                    default_start = max_cost_date
                else:
                    default_start = first_day_of_month
                
                # Ensure the default range is valid
                if default_start > default_end:
                    default_start = default_end
                
                # Create date input with valid defaults
                cost_date_range = st.date_input(
                    "Chọn Khoảng thời gian",
                    [default_start, default_end],
                    min_value=min_cost_date,
                    max_value=max_cost_date,
                    key="material_cost_date_range"
                )
            except Exception as e:
                # Fallback if date parsing fails
                st.error(f"Lỗi khi xử lý ngày tháng: {str(e)}")
                # Use a simple date range selection without defaults
                cost_date_range = st.date_input(
                    "Chọn Khoảng thời gian",
                    key="material_cost_date_range_fallback"
                )
            
            # Only proceed if we have a valid date range
            if isinstance(cost_date_range, (list, tuple)) and len(cost_date_range) == 2:
                start_date, end_date = cost_date_range
                
                # Convert dates to string format for filtering
                start_date_str = start_date.strftime('%Y-%m-%d')
                end_date_str = end_date.strftime('%Y-%m-%d')
                
                # Filter material costs
                filtered_costs_display = material_costs_display[
                    (material_costs_display['Ngày'] >= start_date_str) & 
                    (material_costs_display['Ngày'] <= end_date_str)
                ]
                
                filtered_costs_df = material_costs_df[
                    (material_costs_df['date'] >= start_date_str) & 
                    (material_costs_df['date'] <= end_date_str)
                ]
                
                # Check if we have data in the selected range
                if filtered_costs_df.empty:
                    st.info(f"Không có dữ liệu chi phí nhập nguyên liệu trong khoảng từ {start_date_str} đến {end_date_str}.")
                else:
                    # Show total cost for period
                    total_period_cost = filtered_costs_df['total_cost'].sum()
                    st.metric("Tổng Chi phí nhập Nguyên liệu", f"{total_period_cost:,.0f} VND")
                    
                    # Display filtered costs
                    st.dataframe(filtered_costs_display)
                    
                    # Group costs by material
                    material_grouped = filtered_costs_df.groupby('material_id').agg({
                        'quantity': 'sum',
                        'total_cost': 'sum'
                    }).reset_index()
                    
                    # Get material names (safely)
                    material_names = {}
                    if not st.session_state.materials.empty:
                        for _, material in st.session_state.materials.iterrows():
                            material_names[material['material_id']] = material['name']
                    
                    # Format for display
                    material_summary = pd.DataFrame({
                        'Mã Nguyên liệu': material_grouped['material_id'],
                        'Tên Nguyên liệu': material_grouped['material_id'].apply(
                            lambda x: material_names.get(x, x)
                        ),
                        'Tổng Số lượng': material_grouped['quantity'],
                        'Tổng Chi phí': material_grouped['total_cost'].apply(lambda x: f"{x:,.0f} VND")
                    })
                    
                    st.subheader("Chi phí theo Nguyên liệu")
                    st.dataframe(material_summary)
        else:
            st.info("Chưa có dữ liệu chi phí nhập nguyên liệu. Vui lòng nhập nguyên liệu vào kho để theo dõi chi phí.")
    
    with income_tab3:
        st.subheader("Chi phí Nhân công")
        
        # Add form to record new labor costs
        st.write("### Thêm Chi phí Nhân công")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Date of labor cost
            labor_date = st.date_input(
                "Ngày", 
                value=datetime.date.today(),
                key="labor_cost_date"
            ).strftime("%Y-%m-%d")
            
            # Worker name
            worker_name = st.text_input("Người thực hiện", key="worker_name")
        
        with col2:
            # Job description
            job_description = st.text_input("Mô tả công việc", key="job_description")
            
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Hours or quantity
            hours = st.number_input(
                "Số giờ/khối lượng", 
                min_value=0.1, 
                value=1.0, 
                step=0.1,
                key="labor_hours"
            )
        
        with col2:
            # Rate per hour/unit
            rate = st.number_input(
                "Đơn giá (VND/đơn vị)", 
                min_value=1000, 
                value=50000, 
                step=5000,
                key="labor_rate"
            )
            
        with col3:
            # Calculate total cost automatically
            total_labor_cost = hours * rate
            st.write("**Tổng chi phí:**")
            st.write(f"{total_labor_cost:,.0f} VND")
        
        # Additional notes
        notes = st.text_area("Ghi chú", key="labor_notes")
        
        # Add button to save labor cost
        if st.button("Lưu Chi phí Nhân công"):
            if not worker_name:
                st.error("Vui lòng nhập tên người thực hiện")
            elif not job_description:
                st.error("Vui lòng nhập mô tả công việc")
            else:
                # Add new labor cost record
                new_labor_cost = pd.DataFrame({
                    'date': [labor_date],
                    'worker_name': [worker_name],
                    'description': [job_description],
                    'hours': [hours],
                    'unit_rate': [rate],
                    'total_cost': [total_labor_cost],
                    'notes': [notes]
                })
                
                # Update session state
                if 'labor_costs' not in st.session_state:
                    st.session_state.labor_costs = new_labor_cost
                else:
                    st.session_state.labor_costs = pd.concat([st.session_state.labor_costs, new_labor_cost], ignore_index=True)
                
                st.success(f"Đã lưu chi phí nhân công: {total_labor_cost:,.0f} VND")
                
                # Save to storage
                save_dataframe(st.session_state.labor_costs, "labor_costs.csv")

                # Rerun to update the display immediately
                st.rerun()
        
        # Display existing labor costs
        if 'labor_costs' in st.session_state and not st.session_state.labor_costs.empty:
            st.write("### Chi phí Nhân công Đã Lưu")
            
            # Format labor costs for display
            labor_costs_df = st.session_state.labor_costs.copy()
            
            # Date filter for labor costs
            try:
                # Get min and max dates from data
                min_labor_date_str = labor_costs_df['date'].min()
                max_labor_date_str = labor_costs_df['date'].max()
                
                min_labor_date = datetime.datetime.strptime(min_labor_date_str, '%Y-%m-%d').date()
                max_labor_date = datetime.datetime.strptime(max_labor_date_str, '%Y-%m-%d').date()
                
                # Create date input with valid defaults
                labor_date_range = st.date_input(
                    "Chọn Khoảng thời gian",
                    [min_labor_date, max_labor_date],
                    min_value=min_labor_date,
                    max_value=max_labor_date,
                    key="labor_cost_date_range"
                )
                
                if isinstance(labor_date_range, (list, tuple)) and len(labor_date_range) == 2:
                    start_date, end_date = labor_date_range
                    
                    # Convert dates to string format for filtering
                    start_date_str = start_date.strftime('%Y-%m-%d')
                    end_date_str = end_date.strftime('%Y-%m-%d')
                    
                    # Filter labor costs
                    filtered_labor_costs = labor_costs_df[
                        (labor_costs_df['date'] >= start_date_str) & 
                        (labor_costs_df['date'] <= end_date_str)
                    ]
                    
                    if not filtered_labor_costs.empty:
                        # Display total labor cost for the period
                        total_period_labor = filtered_labor_costs['total_cost'].sum()
                        st.metric("Tổng Chi phí Nhân công", f"{total_period_labor:,.0f} VND")
                        
                        # Format for display
                        display_labor_costs = pd.DataFrame({
                            'ID': filtered_labor_costs.index,
                            'Ngày': filtered_labor_costs['date'],
                            'Người thực hiện': filtered_labor_costs['worker_name'],
                            'Mô tả công việc': filtered_labor_costs['description'],
                            'Số giờ/khối lượng': filtered_labor_costs['hours'],
                            'Đơn giá': filtered_labor_costs['unit_rate'].apply(lambda x: f"{x:,.0f} VND"),
                            'Tổng chi phí': filtered_labor_costs['total_cost'].apply(lambda x: f"{x:,.0f} VND")
                        })
                        
                        # Display the filtered data
                        st.dataframe(display_labor_costs)
                        
                        # Thêm chức năng xóa chi phí nhân công
                        st.subheader("Xóa Chi phí Nhân công")
                        
                        # Chọn ID dòng cần xóa
                        if len(filtered_labor_costs) > 0:
                            delete_options = []
                            for idx, row in filtered_labor_costs.iterrows():
                                delete_options.append(f"ID: {idx} - {row['date']} - {row['worker_name']} - {row['description']} - {row['total_cost']:,.0f} VND")
                            
                            selected_labor_to_delete = st.selectbox(
                                "Chọn chi phí nhân công để xóa",
                                options=delete_options,
                                key="delete_labor_select"
                            )
                            
                            if selected_labor_to_delete:
                                # Lấy ID từ chuỗi đã chọn
                                labor_id = int(selected_labor_to_delete.split(" - ")[0].replace("ID: ", ""))
                                
                                # Hiển thị thông tin chi tiết về dòng sẽ xóa
                                labor_to_delete = labor_costs_df.loc[labor_id]
                                st.write(f"**Chi tiết chi phí sẽ xóa:**")
                                st.write(f"- Ngày: {labor_to_delete['date']}")
                                st.write(f"- Người thực hiện: {labor_to_delete['worker_name']}")
                                st.write(f"- Mô tả: {labor_to_delete['description']}")
                                st.write(f"- Tổng chi phí: {labor_to_delete['total_cost']:,.0f} VND")
                                
                                # Nút xác nhận xóa
                                confirm_delete = st.checkbox("Tôi xác nhận muốn xóa chi phí này", key="confirm_delete_labor")
                                
                                if st.button("Xóa Chi phí Nhân công", key="delete_labor_button"):
                                    if confirm_delete:
                                        # Xóa dòng chi phí được chọn
                                        st.session_state.labor_costs = st.session_state.labor_costs.drop(labor_id)
                                        
                                        # Reset index sau khi xóa
                                        st.session_state.labor_costs = st.session_state.labor_costs.reset_index(drop=True)
                                        
                                        # Lưu lại dữ liệu
                                        save_dataframe(st.session_state.labor_costs, "labor_costs.csv")
                                        
                                        st.success(f"Đã xóa chi phí nhân công thành công!")
                                        st.rerun()
                                    else:
                                        st.error("Vui lòng xác nhận việc xóa bằng cách đánh dấu vào ô xác nhận.")
                        
                        # Group by worker
                        worker_grouped = filtered_labor_costs.groupby('worker_name').agg({
                            'hours': 'sum',
                            'total_cost': 'sum'
                        }).reset_index()
                        
                        # Format for display
                        worker_summary = pd.DataFrame({
                            'Người thực hiện': worker_grouped['worker_name'],
                            'Tổng giờ/khối lượng': worker_grouped['hours'],
                            'Tổng chi phí': worker_grouped['total_cost'].apply(lambda x: f"{x:,.0f} VND")
                        })
                        
                        st.subheader("Chi phí theo Người thực hiện")
                        st.dataframe(worker_summary)
                    else:
                        st.info(f"Không có dữ liệu chi phí nhân công trong khoảng từ {start_date_str} đến {end_date_str}.")
            except Exception as e:
                st.error(f"Lỗi khi xử lý dữ liệu chi phí nhân công: {str(e)}")
                st.info("Vui lòng kiểm tra lại dữ liệu chi phí nhân công.")
        else:
            st.info("Chưa có dữ liệu chi phí nhân công. Vui lòng thêm chi phí nhân công để theo dõi.")

    # Thêm tab Chi phí Marketing
    with income_tab4:
        st.subheader("Chi phí Marketing")
        
        # Form thêm chi phí marketing mới
        st.write("### Thêm Chi phí Marketing")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Ngày chi phí
            marketing_date = st.date_input(
                "Ngày", 
                value=datetime.date.today(),
                key="marketing_cost_date"
            ).strftime("%Y-%m-%d")
            
            # Tên chiến dịch
            campaign_name = st.text_input("Tên chiến dịch", key="campaign_name")
        
        with col2:
            # Mô tả chi phí
            marketing_description = st.text_input("Mô tả chi tiết", key="marketing_description")
            
            # Nền tảng marketing
            platform_options = ["Facebook", "Google", "TikTok", "Instagram", "Báo/Tạp chí", "Biển quảng cáo", "Khác"]
            platform = st.selectbox("Nền tảng", options=platform_options, key="marketing_platform")
            
            if platform == "Khác":
                custom_platform = st.text_input("Nhập tên nền tảng", key="custom_platform")
                platform = custom_platform
        
        # Chi phí
        amount = st.number_input(
            "Chi phí (VND)", 
            min_value=1000, 
            value=100000, 
            step=10000,
            key="marketing_amount"
        )
        
        # Ghi chú bổ sung
        marketing_notes = st.text_area("Ghi chú", key="marketing_notes")
        
        # Nút lưu chi phí
        if st.button("Lưu Chi phí Marketing"):
            if not campaign_name:
                st.error("Vui lòng nhập tên chiến dịch")
            elif not marketing_description:
                st.error("Vui lòng nhập mô tả chi tiết")
            else:
                # Tạo bản ghi chi phí mới
                new_marketing_cost = pd.DataFrame({
                    'date': [marketing_date],
                    'campaign_name': [campaign_name],
                    'description': [marketing_description],
                    'platform': [platform],
                    'amount': [amount],
                    'notes': [marketing_notes]
                })
                
                # Cập nhật session state
                if 'marketing_costs' not in st.session_state:
                    st.session_state.marketing_costs = new_marketing_cost
                else:
                    st.session_state.marketing_costs = pd.concat([st.session_state.marketing_costs, new_marketing_cost], ignore_index=True)
                
                st.success(f"Đã lưu chi phí marketing: {amount:,.0f} VND")
                
                # Lưu dữ liệu
                save_dataframe(st.session_state.marketing_costs, "marketing_costs.csv")

                # Rerun to update the display immediately
                st.rerun()
        
        # Hiển thị chi phí marketing hiện có
        if 'marketing_costs' in st.session_state and not st.session_state.marketing_costs.empty:
            st.write("### Chi phí Marketing Đã Lưu")
            
            # Format chi phí marketing để hiển thị
            marketing_costs_df = st.session_state.marketing_costs.copy()
            
            # Bộ lọc ngày
            try:
                # Lấy ngày min và max từ dữ liệu
                min_marketing_date_str = marketing_costs_df['date'].min()
                max_marketing_date_str = marketing_costs_df['date'].max()
                
                min_marketing_date = datetime.datetime.strptime(min_marketing_date_str, '%Y-%m-%d').date()
                max_marketing_date = datetime.datetime.strptime(max_marketing_date_str, '%Y-%m-%d').date()
                
                # Tạo bộ chọn khoảng thời gian
                marketing_date_range = st.date_input(
                    "Chọn Khoảng thời gian",
                    [min_marketing_date, max_marketing_date],
                    min_value=min_marketing_date,
                    max_value=max_marketing_date,
                    key="marketing_cost_date_range"
                )
                
                if isinstance(marketing_date_range, (list, tuple)) and len(marketing_date_range) == 2:
                    start_date, end_date = marketing_date_range
                    
                    # Chuyển đổi ngày sang định dạng chuỗi để lọc
                    start_date_str = start_date.strftime('%Y-%m-%d')
                    end_date_str = end_date.strftime('%Y-%m-%d')
                    
                    # Lọc chi phí marketing
                    filtered_marketing_costs = marketing_costs_df[
                        (marketing_costs_df['date'] >= start_date_str) & 
                        (marketing_costs_df['date'] <= end_date_str)
                    ]
                    
                    if not filtered_marketing_costs.empty:
                        # Hiển thị tổng chi phí cho khoảng thời gian
                        total_period_marketing = filtered_marketing_costs['amount'].sum()
                        st.metric("Tổng Chi phí Marketing", f"{total_period_marketing:,.0f} VND")
                        
                        # Format để hiển thị
                        display_marketing_costs = pd.DataFrame({
                            'ID': filtered_marketing_costs.index,
                            'Ngày': filtered_marketing_costs['date'],
                            'Chiến dịch': filtered_marketing_costs['campaign_name'],
                            'Mô tả': filtered_marketing_costs['description'],
                            'Nền tảng': filtered_marketing_costs['platform'],
                            'Chi phí': filtered_marketing_costs['amount'].apply(lambda x: f"{x:,.0f} VND")
                        })
                        
                        # Hiển thị dữ liệu đã lọc
                        st.dataframe(display_marketing_costs)
                        
                        # Thêm chức năng xóa chi phí marketing
                        st.subheader("Xóa Chi phí Marketing")
                        
                        # Chọn ID dòng cần xóa
                        if len(filtered_marketing_costs) > 0:
                            delete_marketing_options = []
                            for idx, row in filtered_marketing_costs.iterrows():
                                delete_marketing_options.append(f"ID: {idx} - {row['date']} - {row['campaign_name']} - {row['platform']} - {row['amount']:,.0f} VND")
                            
                            selected_marketing_to_delete = st.selectbox(
                                "Chọn chi phí marketing để xóa",
                                options=delete_marketing_options,
                                key="delete_marketing_select"
                            )
                            
                            if selected_marketing_to_delete:
                                # Lấy ID từ chuỗi đã chọn
                                marketing_id = int(selected_marketing_to_delete.split(" - ")[0].replace("ID: ", ""))
                                
                                # Hiển thị thông tin chi tiết về dòng sẽ xóa
                                marketing_to_delete = marketing_costs_df.loc[marketing_id]
                                st.write(f"**Chi tiết chi phí sẽ xóa:**")
                                st.write(f"- Ngày: {marketing_to_delete['date']}")
                                st.write(f"- Chiến dịch: {marketing_to_delete['campaign_name']}")
                                st.write(f"- Nền tảng: {marketing_to_delete['platform']}")
                                st.write(f"- Chi phí: {marketing_to_delete['amount']:,.0f} VND")
                                
                                # Nút xác nhận xóa
                                confirm_delete_marketing = st.checkbox("Tôi xác nhận muốn xóa chi phí này", key="confirm_delete_marketing")
                                
                                if st.button("Xóa Chi phí Marketing", key="delete_marketing_button"):
                                    if confirm_delete_marketing:
                                        # Xóa dòng chi phí được chọn
                                        st.session_state.marketing_costs = st.session_state.marketing_costs.drop(marketing_id)
                                        
                                        # Reset index sau khi xóa
                                        st.session_state.marketing_costs = st.session_state.marketing_costs.reset_index(drop=True)
                                        
                                        # Lưu lại dữ liệu
                                        save_dataframe(st.session_state.marketing_costs, "marketing_costs.csv")
                                        
                                        st.success(f"Đã xóa chi phí marketing thành công!")
                                        st.rerun()
                                    else:
                                        st.error("Vui lòng xác nhận việc xóa bằng cách đánh dấu vào ô xác nhận.")
                        
                        # Nhóm theo nền tảng
                        platform_grouped = filtered_marketing_costs.groupby('platform').agg({
                            'amount': 'sum'
                        }).reset_index()
                        
                        # Format để hiển thị
                        platform_summary = pd.DataFrame({
                            'Nền tảng': platform_grouped['platform'],
                            'Tổng chi phí': platform_grouped['amount'].apply(lambda x: f"{x:,.0f} VND")
                        })
                        
                        st.subheader("Chi phí theo Nền tảng")
                        st.dataframe(platform_summary)
                        
                        # Biểu đồ chi phí theo nền tảng
                        st.subheader("Biểu đồ Chi phí theo Nền tảng")
                        chart_data = pd.DataFrame({
                            'Nền tảng': platform_grouped['platform'],
                            'Chi phí': platform_grouped['amount']
                        })
                        st.bar_chart(chart_data.set_index('Nền tảng'))
                        
                        # Nhóm theo chiến dịch
                        campaign_grouped = filtered_marketing_costs.groupby('campaign_name').agg({
                            'amount': 'sum'
                        }).reset_index()
                        
                        # Format để hiển thị
                        campaign_summary = pd.DataFrame({
                            'Chiến dịch': campaign_grouped['campaign_name'],
                            'Tổng chi phí': campaign_grouped['amount'].apply(lambda x: f"{x:,.0f} VND")
                        })
                        
                        st.subheader("Chi phí theo Chiến dịch")
                        st.dataframe(campaign_summary)

                        # Thêm chức năng xóa chi phí marketing
                        st.subheader("Xóa Chi phí Marketing")

                        # Chọn ID dòng cần xóa
                        if len(filtered_marketing_costs) > 0:
                            delete_marketing_options = []
                            for idx, row in filtered_marketing_costs.iterrows():
                                delete_marketing_options.append(f"ID: {idx} - {row['date']} - {row['campaign_name']} - {row['platform']} - {row['amount']:,.0f} VND")
                            
                            selected_marketing_to_delete = st.selectbox(
                                "Chọn chi phí marketing để xóa",
                                options=delete_marketing_options,
                                key="delete_marketing_select"
                            )
                            
                            if selected_marketing_to_delete:
                                # Lấy ID từ chuỗi đã chọn
                                marketing_id = int(selected_marketing_to_delete.split(" - ")[0].replace("ID: ", ""))
                                
                                # Hiển thị thông tin chi tiết về dòng sẽ xóa
                                marketing_to_delete = marketing_costs_df.loc[marketing_id]
                                st.write(f"**Chi tiết chi phí sẽ xóa:**")
                                st.write(f"- Ngày: {marketing_to_delete['date']}")
                                st.write(f"- Chiến dịch: {marketing_to_delete['campaign_name']}")
                                st.write(f"- Nền tảng: {marketing_to_delete['platform']}")
                                st.write(f"- Chi phí: {marketing_to_delete['amount']:,.0f} VND")
                                
                                # Nút xác nhận xóa
                                confirm_delete_marketing = st.checkbox("Tôi xác nhận muốn xóa chi phí này", key="confirm_delete_marketing")
                                
                                if st.button("Xóa Chi phí Marketing", key="delete_marketing_button"):
                                    if confirm_delete_marketing:
                                        # Xóa dòng chi phí được chọn
                                        st.session_state.marketing_costs = st.session_state.marketing_costs.drop(marketing_id)
                                        
                                        # Reset index sau khi xóa
                                        st.session_state.marketing_costs = st.session_state.marketing_costs.reset_index(drop=True)
                                        
                                        # Lưu lại dữ liệu
                                        save_dataframe(st.session_state.marketing_costs, "marketing_costs.csv")
                                        
                                        st.success(f"Đã xóa chi phí marketing thành công!")
                                        st.rerun()
                                    else:
                                        st.error("Vui lòng xác nhận việc xóa bằng cách đánh dấu vào ô xác nhận.")

                    else:
                        st.info(f"Không có dữ liệu chi phí marketing trong khoảng từ {start_date_str} đến {end_date_str}.")
            except Exception as e:
                st.error(f"Lỗi khi xử lý dữ liệu chi phí marketing: {str(e)}")
                st.info("Vui lòng kiểm tra lại dữ liệu chi phí marketing.")
        else:
            st.info("Chưa có dữ liệu chi phí marketing. Vui lòng thêm chi phí marketing để theo dõi.")

# Materials Inventory Tab - Updated with Out-of-Stock Notifications
elif tab_selection == "Kho Nguyên liệu":
    st.header("Kho Nguyên liệu")
    
    # In the Kho Nguyên liệu tab, before displaying materials
    if 'used_quantity' not in st.session_state.materials.columns:
        st.session_state.materials['used_quantity'] = 0.0

    # Check for out-of-stock or low stock items immediately
    if not st.session_state.materials.empty:
        out_of_stock_items = []
        low_stock_items = []
        
        for _, material in st.session_state.materials.iterrows():
            # Get initial quantity - use price_per_unit * quantity as a rough estimate of initial value
            initial_quantity = material.get('initial_quantity', None)
            
            # If initial_quantity is not available, estimate it from used_quantity
            if initial_quantity is None or initial_quantity <= 0:
                initial_quantity = material['quantity'] + material.get('used_quantity', 0)
                    
            # Calculate exact percentage remaining
            percentage_remaining = (material['quantity'] / initial_quantity * 100) if initial_quantity > 0 else 100
            
            # Check stock levels more precisely
            if material['quantity'] <= 0:
                out_of_stock_items.append(material['name'])
            elif percentage_remaining <= 10.0:  # Exactly 10% or less
                # Skip this warning for new products
                used_quantity = material.get('used_quantity', 0)
                is_new_product = used_quantity == 0 and material['quantity'] > 0
                
                if not is_new_product:
                    # Format percentage to exactly 1 decimal place for display
                    low_stock_items.append(f"{material['name']} ({percentage_remaining:.1f}% còn lại)")
        
        # Show notifications for out-of-stock items
        if out_of_stock_items:
            st.error(f"⚠️ **Cảnh báo: Các nguyên liệu đã hết hàng:** {', '.join(out_of_stock_items)}")
        
        # Show notifications for low stock items
        if low_stock_items:
            st.warning(f"⚠️ **Cảnh báo: Các nguyên liệu sắp hết hàng (10% hoặc ít hơn số lượng ban đầu):** {', '.join(low_stock_items)}")
    
    # Initialize material costs tracking if not exists
    if 'material_costs' not in st.session_state:
        st.session_state.material_costs = pd.DataFrame(columns=[
            'date', 'material_id', 'quantity', 'total_cost', 'supplier'
        ])
    
    mat_tab1, mat_tab2, mat_tab3, mat_tab4 = st.tabs(["Xem Kho", "Cập nhật Kho", "Nhập Nguyên liệu", "Xóa Nguyên liệu"])
    
    with mat_tab1:
        st.subheader("Kho hiện tại")
        
        # Create a safer display version without style function
        if not st.session_state.materials.empty:
            # Create a copy of the materials dataframe for display
            materials_display = st.session_state.materials.copy()
            
            # Add status column
            def get_status(row):
                quantity = row['quantity']
                
                # If quantity is zero or negative, it's out of stock
                if quantity <= 0:
                    return "Hết hàng"
                
                # Get initial quantity from the row or calculate it
                initial_quantity = row.get('initial_quantity', None)
                
                # If initial_quantity is not available, estimate it from used_quantity
                if initial_quantity is None or initial_quantity <= 0:
                    initial_quantity = quantity + row.get('used_quantity', 0)
                
                # Calculate exact percentage remaining
                percentage_remaining = (quantity / initial_quantity * 100) if initial_quantity > 0 else 100
                
                # Check if it's a new product (nothing used yet)
                is_new_product = row.get('used_quantity', 0) == 0 and quantity > 0
                
                # Determine status based on exact percentage
                if percentage_remaining <= 10.0 and not is_new_product:  # Exactly 10% or less
                    return "Sắp hết hàng"
                elif percentage_remaining <= 30.0 and not is_new_product:  # Between 10% and 30%
                    return "Hàng trung bình"
                else:
                    return "Còn hàng"

            # Apply the function to the materials dataframe
            # We need to pass the whole row, not just the quantity
            materials_display['Trạng thái'] = materials_display.apply(get_status, axis=1)
            
            # Create a cleaner display version
            display_df = pd.DataFrame({
                'Mã nguyên liệu': materials_display['material_id'],
                'Tên': materials_display['name'],
                'Đơn vị': materials_display['unit'],
                'Số lượng': materials_display['quantity'].apply(lambda x: f"{x:.5f}"),  # Exactly 5 decimal places
                'Đã sử dụng': materials_display['used_quantity'].apply(lambda x: f"{x:.5f}"),  # Exactly 5 decimal places
                'Giá/Đơn vị': [f"{price:,.0f} VND" for price in materials_display['price_per_unit']],
                'Trạng thái': materials_display['Trạng thái']
            })
            
            # Display the dataframe
            st.dataframe(display_df)
            
            # Add color coding with HTML instead
            status_counts = materials_display['Trạng thái'].value_counts()
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if 'Hết hàng' in status_counts:
                    st.markdown(f"<div style='background-color:#ff8888;padding:10px;border-radius:5px;'><b>Hết hàng:</b> {status_counts.get('Hết hàng', 0)} mục</div>", unsafe_allow_html=True)
            with col2:
                if 'Sắp hết hàng' in status_counts:
                    st.markdown(f"<div style='background-color:#ffcccc;padding:10px;border-radius:5px;'><b>Sắp hết hàng:</b> {status_counts.get('Sắp hết hàng', 0)} mục</div>", unsafe_allow_html=True)
            with col3:
                if 'Hàng trung bình' in status_counts:
                    st.markdown(f"<div style='background-color:#ffffcc;padding:10px;border-radius:5px;'><b>Hàng trung bình:</b> {status_counts.get('Hàng trung bình', 0)} mục</div>", unsafe_allow_html=True)
            with col4:
                if 'Còn hàng' in status_counts:
                    st.markdown(f"<div style='background-color:#ccffcc;padding:10px;border-radius:5px;'><b>Còn hàng:</b> {status_counts.get('Còn hàng', 0)} mục</div>", unsafe_allow_html=True)
            
            # Summary metrics
            total_value = sum(m['quantity'] * m['price_per_unit'] for _, m in st.session_state.materials.iterrows() if m['quantity'] > 0)
            st.metric("Tổng Giá trị Kho", f"{total_value:,.0f} VND")
            
            # Out of stock list
            if 'Hết hàng' in status_counts or 'Sắp hết hàng' in status_counts:
                st.subheader("Danh sách cần Nhập hàng")
                needs_restock = materials_display[(materials_display['Trạng thái'] == 'Hết hàng') | 
                                                 (materials_display['Trạng thái'] == 'Sắp hết hàng')]
                
                restock_df = pd.DataFrame({
                    'Mã nguyên liệu': needs_restock['material_id'],
                    'Tên': needs_restock['name'],
                    'Đơn vị': needs_restock['unit'],
                    'Số lượng hiện tại': needs_restock['quantity'],
                    'Trạng thái': needs_restock['Trạng thái']
                })
                
                st.dataframe(restock_df)
                
                # Generate shopping list
                if st.button("Tạo Danh sách mua hàng"):
                    shopping_list = ""
                    for _, item in needs_restock.iterrows():
                        current_qty = item['quantity']
                        
                        # Calculate suggested order quantity
                        if current_qty <= 0:
                            suggested_qty = 20  # Standard restock amount for out of stock
                        else:
                            suggested_qty = 20 - current_qty  # Top up to 20 units
                            
                        shopping_list += f"- {item['name']}: {suggested_qty} {item['unit']} " + \
                                        f"(hiện tại: {current_qty}) - " + \
                                        f"Đơn giá tham khảo: {item['price_per_unit']:,.0f} VND\n"
                    
                    # Display the shopping list
                    st.subheader("Danh sách mua hàng đề xuất")
                    st.text_area("Sao chép danh sách này:", shopping_list, height=200)
        else:
            st.info("Chưa có dữ liệu nguyên liệu.")
        
    with mat_tab2:
        st.subheader("Cập nhật Kho")
        
        # Select material to update
        if not st.session_state.materials.empty:
            # Create a list of options for the selectbox
            material_options = []
            for _, material in st.session_state.materials.iterrows():
                # Get initial quantity - use price_per_unit * quantity as a rough estimate of initial value
                initial_quantity = material.get('initial_quantity', None)
                
                # If initial_quantity is not available, estimate it from used_quantity
                if initial_quantity is None or initial_quantity <= 0:
                    initial_quantity = material['quantity'] + material.get('used_quantity', 0)
                        
                # Calculate exact percentage remaining
                percentage_remaining = (material['quantity'] / initial_quantity * 100) if initial_quantity > 0 else 100
                
                # Check if it's a new product (nothing used yet)
                is_new_product = material.get('used_quantity', 0) == 0 and material['quantity'] > 0
                
                # Determine status text based on levels (matching the Xem Kho tab)
                status = ""
                if material['quantity'] <= 0:
                    status = " [HẾT HÀNG]"
                elif percentage_remaining <= 10.0 and not is_new_product:
                    status = f" [SẮP HẾT - {percentage_remaining:.1f}%]"
                elif percentage_remaining <= 30.0 and not is_new_product:
                    status = " [TRUNG BÌNH]"
                        
                material_options.append(f"{material['material_id']} - {material['name']}{status}")
            
            selected_material = st.selectbox(
                "Chọn Nguyên liệu",
                options=material_options,
                key="update_material_select"
            )
            
            if selected_material:
                # Extract material_id from the selection
                selected_material_id = selected_material.split(' - ')[0]
                
                # Find the material data
                material_data = st.session_state.materials[st.session_state.materials['material_id'] == selected_material_id]
                
                if not material_data.empty:
                    material_idx = material_data.index[0]
                    current_quantity = st.session_state.materials.at[material_idx, 'quantity']
                    current_price = st.session_state.materials.at[material_idx, 'price_per_unit']
                    current_used_quantity = st.session_state.materials.at[material_idx, 'used_quantity']
                    
                    # Get initial quantity for percentage calculation
                    initial_quantity = material_data.get('initial_quantity', None).iloc[0] if 'initial_quantity' in material_data.columns else None
                    
                    # If initial_quantity is not available, estimate it from used_quantity
                    if initial_quantity is None or initial_quantity <= 0:
                        initial_quantity = current_quantity + material_data['used_quantity'].iloc[0]
                    
                    # Calculate percentage remaining
                    percentage_remaining = (current_quantity / initial_quantity * 100) if initial_quantity > 0 else 100
                    is_new_product = material_data['used_quantity'].iloc[0] == 0 and current_quantity > 0
                    
                    # Show warning if out of stock or low stock (consistent with tab 1)
                    if current_quantity <= 0:
                        st.error(f"⚠️ Nguyên liệu này đã HẾT HÀNG! Số lượng hiện tại: {current_quantity}")
                    elif percentage_remaining <= 10.0 and not is_new_product:
                        st.warning(f"⚠️ Nguyên liệu này sắp hết hàng! Số lượng hiện tại: {current_quantity} ({percentage_remaining:.1f}% còn lại)")
                    elif percentage_remaining <= 30.0 and not is_new_product:
                        st.info(f"Nguyên liệu này còn hàng ở mức trung bình. Số lượng hiện tại: {current_quantity} ({percentage_remaining:.1f}% còn lại)")
                    else:
                        st.success(f"Nguyên liệu này còn đủ hàng. Số lượng hiện tại: {current_quantity}")
                    
                    # Create a layout for update form
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # Allow negative values for quantity to show the actual negative balance
                        new_quantity = st.number_input("Số lượng Mới", value=float(current_quantity), step=0.1)
                        
                    with col2:
                        new_price = st.number_input("Giá Mới trên một Đơn vị", min_value=1, value=int(current_price), step=1000)
                    
                    with col3:
                        # Thêm trường cập nhật số lượng đã sử dụng
                        new_used_quantity = st.number_input(
                            "Lượng Đã Sử Dụng",
                            value=float(current_used_quantity),
                            min_value=0.0,
                            step=0.1,
                            help="Số lượng đã sử dụng cho các đơn hàng. Chỉ điều chỉnh nếu cần sửa lỗi."
                        )
                    
                    # Display total quantity (current + used)
                    st.info(f"Tổng lượng (hiện tại + đã sử dụng): {new_quantity + new_used_quantity:.5f}")
                    
                    # Get current supplier (if exists in data)
                    current_supplier = ""
                    
                    # Check if there's supplier info in material_costs
                    if 'material_costs' in st.session_state and not st.session_state.material_costs.empty:
                        # Get the most recent entry for this material
                        supplier_data = st.session_state.material_costs[
                            st.session_state.material_costs['material_id'] == selected_material_id
                        ].sort_values('date', ascending=False)
                        
                        if not supplier_data.empty and 'supplier' in supplier_data.columns:
                            current_supplier = supplier_data['supplier'].iloc[0]
                    
                    # Add supplier field
                    new_supplier = st.text_input("Nhà cung cấp", value=current_supplier)
                    
                    if st.button("Cập nhật Nguyên liệu"):
                        # Update the material quantity, price, and used quantity
                        st.session_state.materials.at[material_idx, 'quantity'] = new_quantity
                        st.session_state.materials.at[material_idx, 'price_per_unit'] = new_price
                        st.session_state.materials.at[material_idx, 'used_quantity'] = new_used_quantity
                        
                        # If supplier was updated and not empty, record it in material_costs
                        if new_supplier and new_supplier != current_supplier:
                            if 'material_costs' not in st.session_state:
                                st.session_state.material_costs = pd.DataFrame(columns=[
                                    'date', 'material_id', 'quantity', 'total_cost', 'supplier'
                                ])
                            
                            # Record a supplier update entry with zero quantity/cost
                            supplier_update = pd.DataFrame({
                                'date': [date.today().strftime("%Y-%m-%d")],
                                'material_id': [selected_material_id],
                                'quantity': [0],  # No quantity change
                                'total_cost': [0],  # No cost change
                                'supplier': [new_supplier]  # Updated supplier
                            })
                            
                            st.session_state.material_costs = pd.concat([
                                st.session_state.material_costs, supplier_update
                            ], ignore_index=True)
                            
                            # Save material costs data
                            save_dataframe(st.session_state.material_costs, "material_costs.csv")
                        
                        # Show status messages based on new quantity
                        new_initial_quantity = new_quantity + new_used_quantity
                        percentage_remaining = (new_quantity / new_initial_quantity * 100) if new_initial_quantity > 0 else 100
                        
                        if new_quantity <= 0:
                            st.error(f"Nguyên liệu {selected_material_id} đã được cập nhật nhưng hiện đã HẾT HÀNG!")
                        elif percentage_remaining <= 10.0 and new_used_quantity > 0:
                            st.warning(f"Nguyên liệu {selected_material_id} đã được cập nhật nhưng sắp hết hàng! ({percentage_remaining:.1f}% còn lại)")
                        elif percentage_remaining <= 30.0 and new_used_quantity > 0:
                            st.info(f"Nguyên liệu {selected_material_id} đã được cập nhật! Còn hàng ở mức trung bình ({percentage_remaining:.1f}% còn lại)")
                        else:
                            st.success(f"Nguyên liệu {selected_material_id} đã được cập nhật thành công!")
                        
                        # Save materials data
                        save_dataframe(st.session_state.materials, "materials.csv")
        else:
            st.info("Chưa có dữ liệu nguyên liệu để cập nhật.")

    with mat_tab3:
        st.subheader("Nhập Nguyên liệu")

        col1, col2 = st.columns(2)
        
        with col1:
            # Date of import
            import_date = st.date_input(
                "Ngày Nhập", 
                value=datetime.date.today(),
                key="material_import_date"
            ).strftime("%Y-%m-%d")
            
            # Supplier information
            supplier = st.text_input("Nhà cung cấp", key="material_supplier")
        
        # Add radio buttons to select between importing existing material or creating new material
        import_option = st.radio(
            "Lựa chọn:",
            ["Nhập kho nguyên liệu hiện có", "Thêm và nhập nguyên liệu mới"],
            key="import_option"
        )
        
        if import_option == "Nhập kho nguyên liệu hiện có":
            # OPTION 1: IMPORT EXISTING MATERIAL
            if not st.session_state.materials.empty:
                # Create a list of options for the selectbox
                material_options = []
                for _, material in st.session_state.materials.iterrows():
                    # Get initial quantity
                    initial_quantity = material.get('initial_quantity', None)
                    
                    # If initial_quantity is not available, estimate it from used_quantity
                    if initial_quantity is None or initial_quantity <= 0:
                        initial_quantity = material['quantity'] + material.get('used_quantity', 0)
                        
                    # Calculate exact percentage remaining
                    percentage_remaining = (material['quantity'] / initial_quantity * 100) if initial_quantity > 0 else 100
                    
                    # Check if it's a new product (nothing used yet)
                    is_new_product = material.get('used_quantity', 0) == 0 and material['quantity'] > 0
                    
                    # Determine status text based on levels (matching other tabs)
                    status = ""
                    if material['quantity'] <= 0:
                        status = " [HẾT HÀNG]"
                    elif percentage_remaining <= 10.0 and not is_new_product:
                        status = f" [SẮP HẾT - {percentage_remaining:.1f}%]"
                    elif percentage_remaining <= 30.0 and not is_new_product:
                        status = " [TRUNG BÌNH]"
                            
                    material_options.append(f"{material['material_id']} - {material['name']} ({material['unit']}){status}")
                
                selected_material = st.selectbox(
                    "Chọn Nguyên liệu để Nhập",
                    options=material_options,
                    key="import_material_select"
                )
                
                if selected_material:
                    # Extract material_id from the selection
                    selected_material_id = selected_material.split(' - ')[0]
                    
                    # Find the material data
                    material_data = st.session_state.materials[st.session_state.materials['material_id'] == selected_material_id]
                    
                    if not material_data.empty:
                        material_idx = material_data.index[0]
                        current_quantity = st.session_state.materials.at[material_idx, 'quantity']
                        current_unit = st.session_state.materials.at[material_idx, 'unit']
                        current_used_quantity = st.session_state.materials.at[material_idx, 'used_quantity']
                        
                        # Get initial quantity for percentage calculation
                        initial_quantity = material_data.get('initial_quantity', None).iloc[0] if 'initial_quantity' in material_data.columns else None
                        
                        # If initial_quantity is not available, estimate it from used_quantity
                        if initial_quantity is None or initial_quantity <= 0:
                            initial_quantity = current_quantity + material_data['used_quantity'].iloc[0]
                        
                        # Calculate percentage remaining
                        percentage_remaining = (current_quantity / initial_quantity * 100) if initial_quantity > 0 else 100
                        is_new_product = material_data['used_quantity'].iloc[0] == 0 and current_quantity > 0
                        
                        # Show warning if out of stock or low stock (consistent with other tabs)
                        if current_quantity <= 0:
                            st.error(f"⚠️ Nguyên liệu này đã HẾT HÀNG! Số lượng hiện tại: {current_quantity} {current_unit}")
                        elif percentage_remaining <= 10.0 and not is_new_product:
                            st.warning(f"⚠️ Nguyên liệu này sắp hết hàng! Số lượng hiện tại: {current_quantity} {current_unit} ({percentage_remaining:.1f}% còn lại)")
                        elif percentage_remaining <= 30.0 and not is_new_product:
                            st.info(f"Nguyên liệu này còn hàng ở mức trung bình. Số lượng hiện tại: {current_quantity} {current_unit} ({percentage_remaining:.1f}% còn lại)")
                        else:
                            st.success(f"Nguyên liệu này còn đủ hàng. Số lượng hiện tại: {current_quantity} {current_unit}")

                        # Input import details
                        col1, col2 = st.columns(2)
                        with col1:
                            import_quantity = st.number_input(
                                f"Số lượng Nhập ({current_unit})", 
                                min_value=0.1, 
                                value=1.0, 
                                step=0.1,
                                key="import_quantity"
                            )
                        with col2:
                            import_cost = st.number_input(
                                "Tổng Chi phí (VND)", 
                                min_value=1000, 
                                value=100000, 
                                step=1000,
                                key="import_cost"
                            )
                        
                        # Calculate unit price
                        if import_quantity > 0:
                            unit_price = import_cost / import_quantity
                            st.write(f"Giá trên một đơn vị: {unit_price:,.0f} VND/{current_unit}")
                        
                        # Additional notes
                        import_notes = st.text_area("Ghi chú", key="import_notes")
                        
                        # Confirm import
                        if st.button("Xác nhận Nhập kho"):
                            if not supplier:
                                st.error("Vui lòng nhập thông tin nhà cung cấp")
                            elif import_quantity <= 0:
                                st.error("Vui lòng nhập số lượng hợp lệ")
                            else:
                                # Update material quantity
                                new_quantity = current_quantity + import_quantity
                                st.session_state.materials.at[material_idx, 'quantity'] = new_quantity
                                
                                # Update price (weighted average)
                                current_total_value = current_quantity * st.session_state.materials.at[material_idx, 'price_per_unit']
                                new_total_value = current_total_value + import_cost
                                new_price_per_unit = new_total_value / new_quantity if new_quantity > 0 else 0
                                
                                st.session_state.materials.at[material_idx, 'price_per_unit'] = new_price_per_unit
                                
                                # Record the import cost
                                if 'material_costs' not in st.session_state:
                                    st.session_state.material_costs = pd.DataFrame(columns=[
                                        'date', 'material_id', 'quantity', 'total_cost', 'supplier'
                                    ])
                                    
                                new_import = pd.DataFrame({
                                    'date': [import_date],
                                    'material_id': [selected_material_id],
                                    'quantity': [import_quantity],
                                    'total_cost': [import_cost],
                                    'supplier': [supplier]
                                })
                                
                                st.session_state.material_costs = pd.concat([st.session_state.material_costs, new_import], ignore_index=True)
                                
                                st.success(f"Đã nhập {import_quantity} {current_unit} nguyên liệu {selected_material_id} thành công!")
                                st.write(f"Số lượng mới: {new_quantity} {current_unit}")
                                st.write(f"Giá đơn vị mới (trung bình): {new_price_per_unit:,.0f} VND/{current_unit}")
                                # Save materials and material costs data
                                save_dataframe(st.session_state.materials, "materials.csv")
                                save_dataframe(st.session_state.material_costs, "material_costs.csv")
            else:
                st.info("Chưa có dữ liệu nguyên liệu. Vui lòng thêm nguyên liệu mới.")
                
        else:
            # OPTION 2: CREATE AND IMPORT NEW MATERIAL
            st.subheader("Thêm Nguyên liệu Mới")
            
            # Generate a default material ID suggestion
            default_material_id = ""
            if not st.session_state.materials.empty:
                existing_ids = st.session_state.materials['material_id'].tolist()
                # Extract numeric parts from existing IDs that start with "M"
                numeric_parts = []
                for id in existing_ids:
                    if id.startswith("M") and id[1:].isdigit():
                        numeric_parts.append(int(id[1:]))
                
                if numeric_parts:
                    # Suggest next ID number
                    next_id = max(numeric_parts) + 1
                    default_material_id = f"M{next_id:03d}"
                else:
                    default_material_id = "M001"
            else:
                default_material_id = "M001"
            
            new_material_id = st.text_input("Mã Nguyên liệu", value=default_material_id, key="new_material_id")
            new_material_name = st.text_input("Tên Nguyên liệu", key="new_material_name")
            
            # Suggest common units
            unit_options = ["kg", "g", "lít", "ml", "cái", "túi", "gói", "thùng", "hộp", "chai", "Khác"]
            selected_unit_option = st.selectbox("Đơn vị", options=unit_options, key="unit_select")
            
            if selected_unit_option == "Khác":
                new_material_unit = st.text_input("Nhập đơn vị mới:", key="custom_unit")
            else:
                new_material_unit = selected_unit_option
            
            col1, col2 = st.columns(2)
            with col1:
                new_material_quantity = st.number_input("Số lượng nhập", min_value=0.1, value=1.0, step=0.1, key="new_material_quantity")
            with col2:
                new_material_cost = st.number_input("Tổng chi phí (VND)", min_value=1000, value=100000, step=1000, key="new_material_cost")
            
            # Calculate unit price for new material
            if new_material_quantity > 0:
                unit_price = new_material_cost / new_material_quantity
                st.write(f"Giá trên một đơn vị: {unit_price:,.0f} VND/{new_material_unit or selected_unit_option}")
            
            # Additional notes
            new_material_notes = st.text_area("Ghi chú", key="new_material_notes")
            
            if st.button("Thêm và Nhập kho Nguyên liệu Mới"):
                if not new_material_id or not new_material_name or not (new_material_unit or selected_unit_option != "Khác"):
                    st.error("Vui lòng điền đầy đủ thông tin nguyên liệu")
                elif not supplier:
                    st.error("Vui lòng nhập thông tin nhà cung cấp")
                elif new_material_id in st.session_state.materials['material_id'].values:
                    st.error(f"Mã nguyên liệu {new_material_id} đã tồn tại")
                else:
                    # Calculate the price per unit
                    price_per_unit = new_material_cost / new_material_quantity if new_material_quantity > 0 else 0
                    
                    # Add new material
                    new_material = pd.DataFrame({
                        'material_id': [new_material_id],
                        'name': [new_material_name],
                        'unit': [new_material_unit if selected_unit_option == "Khác" else selected_unit_option],
                        'quantity': [new_material_quantity],
                        'price_per_unit': [price_per_unit],
                        'used_quantity': [0.0]
                    })
                    
                    # If materials DataFrame does not exist yet, create it
                    if 'materials' not in st.session_state or st.session_state.materials.empty:
                        st.session_state.materials = new_material
                    else:
                        st.session_state.materials = pd.concat([st.session_state.materials, new_material], ignore_index=True)
                    
                    # Record the initial inventory
                    if 'material_costs' not in st.session_state:
                        st.session_state.material_costs = pd.DataFrame(columns=[
                            'date', 'material_id', 'quantity', 'total_cost', 'supplier'
                        ])
                    
                    initial_import = pd.DataFrame({
                        'date': [import_date],
                        'material_id': [new_material_id],
                        'quantity': [new_material_quantity],
                        'total_cost': [new_material_cost],
                        'supplier': [supplier]
                    })
                    
                    st.session_state.material_costs = pd.concat([st.session_state.material_costs, initial_import], ignore_index=True)
                    
                    unit_display = new_material_unit if selected_unit_option == "Khác" else selected_unit_option
                    st.success(f"Nguyên liệu mới {new_material_id} - {new_material_name} đã được thêm và nhập kho thành công!")
                    st.write(f"Đã nhập: {new_material_quantity} {unit_display}")
                    st.write(f"Giá đơn vị: {price_per_unit:,.0f} VND/{unit_display}")

                    # Save materials and material costs data
                    save_dataframe(st.session_state.materials, "materials.csv")
                    save_dataframe(st.session_state.material_costs, "material_costs.csv")

    with mat_tab4:
        st.subheader("Xóa Nguyên liệu")
        
        if not st.session_state.materials.empty:
            # Tạo danh sách các nguyên liệu để chọn
            material_options = []
            for _, material in st.session_state.materials.iterrows():
                # Xác định trạng thái tương tự như trong tab Xem Kho
                initial_quantity = material.get('initial_quantity', None)
                        
                # Nếu initial_quantity không có sẵn, ước tính từ used_quantity
                if initial_quantity is None or initial_quantity <= 0:
                    initial_quantity = material['quantity'] + material.get('used_quantity', 0)
                                
                # Tính phần trăm còn lại
                percentage_remaining = (material['quantity'] / initial_quantity * 100) if initial_quantity > 0 else 100
                
                # Kiểm tra mức tồn kho
                status = ""
                if material['quantity'] <= 0:
                    status = " [HẾT HÀNG]"
                elif percentage_remaining <= 10.0:
                    # Bỏ qua cảnh báo này cho sản phẩm mới
                    used_quantity = material.get('used_quantity', 0)
                    is_new_product = used_quantity == 0 and material['quantity'] > 0
                    
                    if not is_new_product:
                        status = f" [SẮP HẾT - {percentage_remaining:.1f}%]"
                elif percentage_remaining <= 30.0:
                    used_quantity = material.get('used_quantity', 0)
                    is_new_product = used_quantity == 0 and material['quantity'] > 0
                    
                    if not is_new_product:
                        status = " [TRUNG BÌNH]"
                
                material_options.append(f"{material['material_id']} - {material['name']}{status}")
            
            selected_material = st.selectbox(
                "Chọn Nguyên liệu để Xóa",
                options=material_options,
                key="delete_material_select"
            )
            
            if selected_material:
                # Trích xuất material_id từ lựa chọn
                selected_material_id = selected_material.split(' - ')[0]
                
                # Tìm dữ liệu nguyên liệu
                material_data = st.session_state.materials[st.session_state.materials['material_id'] == selected_material_id]
                
                if not material_data.empty:
                    material_info = material_data.iloc[0]
                    
                    # Hiển thị thông tin nguyên liệu
                    st.write(f"**Tên nguyên liệu:** {material_info['name']}")
                    st.write(f"**Đơn vị:** {material_info['unit']}")
                    st.write(f"**Số lượng hiện tại:** {material_info['quantity']}")
                    st.write(f"**Giá/Đơn vị:** {material_info['price_per_unit']:,.0f} VND")
                    
                    # Kiểm tra xem nguyên liệu có trong công thức nào không
                    material_in_recipes = selected_material_id in st.session_state.recipes['material_id'].values
                    
                    if material_in_recipes:
                        st.warning("⚠️ Nguyên liệu này đang được sử dụng trong các công thức sản phẩm. Xóa nguyên liệu có thể ảnh hưởng đến sản phẩm.")
                        
                        # Danh sách sản phẩm sử dụng nguyên liệu này
                        product_recipes = st.session_state.recipes[st.session_state.recipes['material_id'] == selected_material_id]
                        product_ids = product_recipes['product_id'].unique()
                        
                        # Lấy tên sản phẩm
                        product_names = []
                        for pid in product_ids:
                            product_data = st.session_state.products[st.session_state.products['product_id'] == pid]
                            if not product_data.empty:
                                product_names.append(f"{pid} - {product_data['name'].iloc[0]}")
                            else:
                                product_names.append(f"{pid}")
                        
                        st.write("**Sản phẩm sử dụng nguyên liệu này:**")
                        for product_name in product_names:
                            st.write(f"- {product_name}")
                    
                    # Xóa xác nhận
                    delete_confirmed = st.checkbox("Tôi hiểu rằng hành động này không thể hoàn tác", key="delete_material_confirm")
                    
                    if st.button("Xóa Nguyên liệu") and delete_confirmed:
                        # 1. Xóa lịch sử chi phí nhập hàng liên quan đến nguyên liệu này
                        if 'material_costs' in st.session_state and not st.session_state.material_costs.empty:
                            st.session_state.material_costs = st.session_state.material_costs[
                                st.session_state.material_costs['material_id'] != selected_material_id
                            ]
                        
                        # 2. Xóa nguyên liệu khỏi bảng materials
                        st.session_state.materials = st.session_state.materials[
                            st.session_state.materials['material_id'] != selected_material_id
                        ]
                        
                        if material_in_recipes:
                            # Hiển thị cảnh báo về công thức bị ảnh hưởng
                            st.warning(f"Các công thức sử dụng nguyên liệu {selected_material_id} sẽ không còn chính xác!")
                        
                        # Lưu dữ liệu sau khi xóa
                        save_dataframe(st.session_state.materials, "materials.csv")
                        save_dataframe(st.session_state.material_costs, "material_costs.csv")
                        
                        st.success(f"Đã xóa nguyên liệu {selected_material_id} thành công!")
                        # Làm mới trang để cập nhật hiển thị
                        st.rerun()
        else:
            st.info("Chưa có dữ liệu nguyên liệu để xóa.")

# Product Management Tab
elif tab_selection == "Quản lý Sản phẩm":
    st.header("Quản lý Sản phẩm")
    
    price_tab1, price_tab2, price_tab3, price_tab4 = st.tabs(["Xem Sản phẩm", "Cập nhật Sản phẩm", "Thêm Sản phẩm Mới", "Xóa Sản phẩm"])
    
    with price_tab1:
        st.subheader("Sản phẩm Hiện tại")
        
        if not st.session_state.products.empty:
            # Display products in a cleaner format
            products_display = pd.DataFrame({
                'Mã sản phẩm': st.session_state.products['product_id'],
                'Tên sản phẩm': st.session_state.products['name'],
                'Đơn vị': st.session_state.products['unit'] if 'unit' in st.session_state.products.columns else "",
                'Giá': [f"{price:,.0f} VND" for price in st.session_state.products['price']],
                'Phân loại': st.session_state.products['category']
            })
            
            st.dataframe(products_display)
            
            # Calculate profitability in a safer way
            if not st.session_state.recipes.empty and not st.session_state.materials.empty:
                st.subheader("Lợi nhuận Sản phẩm")
                
                profit_data = []
                
                for _, product in st.session_state.products.iterrows():
                    product_id = product['product_id']
                    product_recipes = st.session_state.recipes[st.session_state.recipes['product_id'] == product_id]
                    
                    # Calculate cost
                    cost = 0
                    if not product_recipes.empty:
                        for _, recipe in product_recipes.iterrows():
                            material_id = recipe['material_id']
                            quantity = recipe['quantity']
                            
                            material_price_data = st.session_state.materials[st.session_state.materials['material_id'] == material_id]
                            if not material_price_data.empty:
                                material_price = material_price_data['price_per_unit'].iloc[0]
                                cost += quantity * material_price

                    # Thêm chi phí nhân công, khấu hao và chi phí khác từ product_costs
                    # Chỉ áp dụng nếu có dữ liệu product_costs
                    if 'product_costs' in st.session_state and not st.session_state.product_costs.empty:
                        product_cost_data = st.session_state.product_costs[
                            st.session_state.product_costs['product_id'] == product_id
                        ]
                        
                        if not product_cost_data.empty:
                            # Thêm chi phí nhân công (production_fee)
                            if 'production_fee' in product_cost_data.columns:
                                production_fee = product_cost_data['production_fee'].iloc[0]
                                cost += production_fee
                            
                            # Thêm chi phí khác (other_fee)
                            if 'other_fee' in product_cost_data.columns:
                                other_fee = product_cost_data['other_fee'].iloc[0]
                                cost += other_fee
                            
                            # Thêm chi phí khấu hao (Depreciation_fee)
                            if 'Depreciation_fee' in product_cost_data.columns:
                                depreciation_fee = product_cost_data['Depreciation_fee'].iloc[0]
                                cost += depreciation_fee
                    
                    # Calculate profit margin
                    price = product['price']
                    profit = price - cost
                    profit_margin = (profit / price) * 100 if price > 0 else 0
                    
                    profit_data.append({
                        'Mã sản phẩm': product_id,
                        'Tên sản phẩm': product['name'],
                        'Giá bán': f"{price:,.0f} VND",
                        'Chi phí': f"{cost:,.0f} VND",
                        'Lợi nhuận': f"{profit:,.0f} VND",
                        'Tỷ suất LN': f"{profit_margin:.2f}%"
                    })
                
                if profit_data:
                    st.dataframe(pd.DataFrame(profit_data))
                else:
                    st.info("Không thể tính toán dữ liệu lợi nhuận.")
            else:
                st.info("Chưa có đủ dữ liệu công thức hoặc nguyên liệu để tính lợi nhuận.")
        else:
            st.info("Chưa có dữ liệu sản phẩm.")
    
    with price_tab2:
        st.subheader("Cập nhật Sản phẩm")
        
        if not st.session_state.products.empty:
            # Create a list of options for the selectbox
            product_options = []
            for _, product in st.session_state.products.iterrows():
                product_options.append(f"{product['product_id']} - {product['name']}")
            
            selected_product = st.selectbox(
                "Chọn Sản phẩm",
                options=product_options,
                key="update_product_select"
            )
            
            if selected_product:
                # Extract product_id from the selection
                selected_product_id = selected_product.split(' - ')[0]
                
                # Find the product data
                product_data = st.session_state.products[st.session_state.products['product_id'] == selected_product_id]
                
                if not product_data.empty:
                    product_idx = product_data.index[0]
                    current_product = product_data.iloc[0]
                    
                    st.write("### Thông tin cơ bản")
                    col1, col2 = st.columns(2)
                    with col1:
                        new_product_name = st.text_input("Tên Sản phẩm", value=current_product['name'])
                        new_product_category = st.text_input("Phân loại", value=current_product['category'])
                    with col2:
                        new_price = st.number_input("Giá", min_value=1000, value=int(current_product['price']), step=1000)
                        
                        # Add unit selection for products
                        current_unit = current_product['unit'] if 'unit' in current_product else "cái"
                        unit_options_product = ["cái", "hộp", "kg", "miếng", "gói", "phần", "Khác"]
                        
                        if current_unit in unit_options_product:
                            default_unit_index = unit_options_product.index(current_unit)
                        else:
                            default_unit_index = len(unit_options_product) - 1  # "Khác"
                            
                        selected_unit_option_product = st.selectbox(
                            "Đơn vị Sản phẩm", 
                            options=unit_options_product, 
                            index=default_unit_index,
                            key="update_product_unit_select"
                        )

                        if selected_unit_option_product == "Khác":
                            product_unit = st.text_input("Nhập đơn vị sản phẩm:", 
                                                        value="" if current_unit in unit_options_product else current_unit,
                                                        key="update_custom_product_unit")
                        else:
                            product_unit = selected_unit_option_product
                    
                    # Get current cost information if it exists
                    current_production_fee = 0
                    current_other_fee = 0
                    current_depreciation_fee = 0
                    
                    if 'product_costs' in st.session_state and not st.session_state.product_costs.empty:
                        product_cost_data = st.session_state.product_costs[
                            st.session_state.product_costs['product_id'] == selected_product_id
                        ]
                        
                        if not product_cost_data.empty:
                            if 'production_fee' in product_cost_data.columns:
                                current_production_fee = product_cost_data['production_fee'].iloc[0]
                            if 'other_fee' in product_cost_data.columns:
                                current_other_fee = product_cost_data['other_fee'].iloc[0]
                            if 'Depreciation_fee' in product_cost_data.columns:
                                current_depreciation_fee = product_cost_data['Depreciation_fee'].iloc[0]
                    
                    # Add direct production fee and other costs inputs
                    st.write("### Chi phí sản xuất")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        production_fee = st.number_input(
                            "Chi phí nhân công (VND)", 
                            min_value=0, 
                            value=int(current_production_fee), 
                            step=1000, 
                            key="update_production_fee"
                        )
                        st.caption("Chi phí liên quan đến quá trình sản xuất")

                    with col2:
                        other_fee = st.number_input(
                            "Chi phí khác (VND)", 
                            min_value=0, 
                            value=int(current_other_fee), 
                            step=1000, 
                            key="update_other_fee"
                        )
                        st.caption("Các chi phí phát sinh khác")

                    with col3:
                        depreciation_fee = st.number_input(
                            "Chi phí khấu hao (VND)", 
                            min_value=0, 
                            value=int(current_depreciation_fee), 
                            step=1000, 
                            key="update_depreciation_fee"
                        )
                        st.caption("Các chi phí khấu hao tài sản cố định")
                    
                    st.write("### Công thức sản phẩm")
                    st.write("Cập nhật số lượng nguyên liệu cần thiết cho sản phẩm này:")
                    
                    # Current recipe
                    current_recipe = st.session_state.recipes[st.session_state.recipes['product_id'] == selected_product_id]
                    
                    # Materials for recipe
                    recipe_materials = []
                    total_material_cost = 0
                    
                    if not st.session_state.materials.empty:
                        for _, material in st.session_state.materials.iterrows():
                            material_id = material['material_id']
                            
                            # Get current quantity from recipe if it exists
                            current_quantity = 0
                            if not current_recipe.empty:
                                material_in_recipe = current_recipe[current_recipe['material_id'] == material_id]
                                if not material_in_recipe.empty:
                                    current_quantity = material_in_recipe['quantity'].iloc[0]
                            
                            col1, col2, col3 = st.columns([3, 1, 2])
                            with col1:
                                st.write(f"{material['name']} ({material['unit']})")
                            with col2:
                                quantity = st.number_input(
                                    f"SL",
                                    min_value=0.0,
                                    value=float(current_quantity),
                                    step=0.00001,
                                    format="%.5f",
                                    key=f"update_recipe_{material_id}"
                                )
                            with col3:
                                if quantity > 0:
                                    material_cost = quantity * material['price_per_unit']
                                    st.write(f"{material_cost:,.0f} VND")
                                    total_material_cost += material_cost
                                else:
                                    st.write("0 VND")
                            
                            if quantity > 0:
                                recipe_materials.append({
                                    'material_id': material_id,
                                    'quantity': quantity
                                })
                    else:
                        st.warning("Không có nguyên liệu nào trong kho. Vui lòng thêm nguyên liệu trước.")
                    
                    # Calculate total cost and suggested price
                    total_cost = total_material_cost + production_fee + other_fee + depreciation_fee

                    # Calculate suggested price with a markup percentage
                    markup_percentage = 66.66
                    markup_multiplier = 1 + (markup_percentage / 100)
                    suggested_price = total_cost * markup_multiplier
                    
                    # Display cost breakdown and suggested price
                    st.write("### Chi phí và Giá đề xuất")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"Chi phí nguyên liệu: **{total_material_cost:,.0f} VND**")
                        st.write(f"Chi phí nhân công: **{production_fee:,.0f} VND**")
                        st.write(f"Chi phí khác: **{other_fee:,.0f} VND**")
                        st.write(f"Chi phí khấu hao tài sản: **{depreciation_fee:,.0f} VND**")
                        st.write(f"**Tổng chi phí: {total_cost:,.0f} VND**")
                    with col2:
                        st.write(f"Tỷ lệ lợi nhuận: **{markup_percentage:.2f}%**")
                        st.write(f"Giá đề xuất: **{suggested_price:,.0f} VND**")
                    
                    # Allow user to use suggested price
                    use_suggested_price = st.checkbox("Sử dụng giá đề xuất", key="update_use_suggested_price")
                    
                    if use_suggested_price:
                        new_price = int(suggested_price)
                        st.write(f"Giá sản phẩm: **{new_price:,.0f} VND**")
                    
                    if st.button("Cập nhật Sản phẩm"):
                        # Update product information
                        st.session_state.products.at[product_idx, 'name'] = new_product_name
                        st.session_state.products.at[product_idx, 'price'] = new_price
                        st.session_state.products.at[product_idx, 'category'] = new_product_category
                        
                        # Update unit
                        if 'unit' in st.session_state.products.columns:
                            st.session_state.products.at[product_idx, 'unit'] = product_unit if selected_unit_option_product == "Khác" else selected_unit_option_product
                        else:
                            # Add unit column if it doesn't exist
                            st.session_state.products['unit'] = ""
                            st.session_state.products.at[product_idx, 'unit'] = product_unit if selected_unit_option_product == "Khác" else selected_unit_option_product
                        
                        # Update or create product cost information
                        if 'product_costs' not in st.session_state:
                            st.session_state.product_costs = pd.DataFrame(columns=[
                                'product_id', 'material_cost', 'production_fee', 'other_fee', 'Depreciation_fee', 'total_cost', 'price'
                            ])
                        
                        # Check if product already has cost info
                        cost_exists = False
                        if not st.session_state.product_costs.empty:
                            cost_data = st.session_state.product_costs[
                                st.session_state.product_costs['product_id'] == selected_product_id
                            ]
                            if not cost_data.empty:
                                cost_idx = cost_data.index[0]
                                cost_exists = True
                                
                                # Update existing cost info
                                st.session_state.product_costs.at[cost_idx, 'material_cost'] = total_material_cost
                                st.session_state.product_costs.at[cost_idx, 'production_fee'] = production_fee
                                st.session_state.product_costs.at[cost_idx, 'other_fee'] = other_fee
                                st.session_state.product_costs.at[cost_idx, 'Depreciation_fee'] = depreciation_fee
                                st.session_state.product_costs.at[cost_idx, 'total_cost'] = total_cost
                                st.session_state.product_costs.at[cost_idx, 'price'] = new_price
                        
                        # If cost info doesn't exist, create it
                        if not cost_exists:
                            new_cost_info = pd.DataFrame({
                                'product_id': [selected_product_id],
                                'material_cost': [total_material_cost],
                                'production_fee': [production_fee],
                                'other_fee': [other_fee],
                                'Depreciation_fee': [depreciation_fee],
                                'total_cost': [total_cost],
                                'price': [new_price]
                            })
                            
                            st.session_state.product_costs = pd.concat([st.session_state.product_costs, new_cost_info], ignore_index=True)
                        
                        # Update recipe information
                        # First, remove all existing recipe entries for this product
                        st.session_state.recipes = st.session_state.recipes[
                            st.session_state.recipes['product_id'] != selected_product_id
                        ]
                        
                        # Then add the new recipe entries
                        if recipe_materials:
                            recipe_rows = []
                            for material in recipe_materials:
                                recipe_rows.append({
                                    'product_id': selected_product_id,
                                    'material_id': material['material_id'],
                                    'quantity': material['quantity']
                                })
                            
                            new_recipes = pd.DataFrame(recipe_rows)
                            st.session_state.recipes = pd.concat([st.session_state.recipes, new_recipes], ignore_index=True)
                        
                        # Save data
                        save_dataframe(st.session_state.products, "products.csv")
                        save_dataframe(st.session_state.recipes, "recipes.csv")
                        save_dataframe(st.session_state.product_costs, "product_costs.csv")
                        
                        st.success(f"Sản phẩm {selected_product_id} đã được cập nhật thành công!")
        else:
            st.info("Chưa có dữ liệu sản phẩm để cập nhật.")

    with price_tab3:
        st.subheader("Thêm Sản phẩm Mới")
        
        # New product form
        new_product_id = st.text_input("Mã Sản phẩm (vd: P005)", key="new_product_id")
        new_product_name = st.text_input("Tên Sản phẩm", key="new_product_name")
        new_product_category = st.text_input("Phân loại", key="new_product_category")

        # Add unit selection for products
        unit_options_product = ["cái", "hộp", "kg", "miếng", "gói", "phần", "Khác"]
        selected_unit_option_product = st.selectbox("Đơn vị Sản phẩm", options=unit_options_product, key="product_unit_select")

        if selected_unit_option_product == "Khác":
            product_unit = st.text_input("Nhập đơn vị sản phẩm mới:", key="custom_product_unit")
        else:
            product_unit = selected_unit_option_product
        
        # Add direct production fee and other costs inputs
        col1, col2, col3 = st.columns(3)
        with col1:
            production_fee = st.number_input(
                "Chi phí nhân công (VND)", 
                min_value=0, 
                value=10000, 
                step=1000, 
                key="production_fee"
            )
            st.caption("Chi phí liên quan đến quá trình sản xuất")
            st.text(f"Giá trị hiện tại: {production_fee:,} VND")

        with col2:
            other_fee = st.number_input(
                "Chi phí khác (VND)", 
                min_value=0, 
                value=5000, 
                step=1000, 
                key="other_fee"
            )
            st.caption("Các chi phí phát sinh khác")
            st.text(f"Giá trị hiện tại: {other_fee:,} VND")

        with col3:
            Depreciation_fee = st.number_input(
                "Chi phí khấu hao (VND)", 
                min_value=0, 
                value=5000, 
                step=1000, 
                key="Depreciation_fee"
            )
            st.caption("Các chi phí khấu hao tài sản cố định")
            st.text(f"Giá trị hiện tại: {Depreciation_fee:,} VND")
                
        st.write("### Công thức")
        st.write("Chọn nguyên liệu và số lượng cần thiết cho sản phẩm này:")
        
        # Materials for recipe
        recipe_materials = []
        total_material_cost = 0
        
        if not st.session_state.materials.empty:
            for _, material in st.session_state.materials.iterrows():
                col1, col2, col3 = st.columns([3, 1, 2])
                with col1:
                    st.write(f"{material['name']} ({material['unit']})")
                with col2:
                    quantity = st.number_input(
                        f"SL",
                        min_value=0.0,
                        value=0.0,
                        step=0.00001,
                        format="%.5f",
                        key=f"new_recipe_{material['material_id']}"
                    )
                with col3:
                    if quantity > 0:
                        material_cost = quantity * material['price_per_unit']
                        st.write(f"{material_cost:,.0f} VND")
                        total_material_cost += material_cost
                    else:
                        st.write("0 VND")
                
                if quantity > 0:
                    recipe_materials.append({
                        'material_id': material['material_id'],
                        'quantity': quantity
                    })
        else:
            st.warning("Không có nguyên liệu nào trong kho. Vui lòng thêm nguyên liệu trước.")
        
        # Calculate total cost and suggested price
        total_cost = total_material_cost + production_fee + other_fee + Depreciation_fee

        # Calculate suggested price with a markup percentage
        markup_percentage = 66.66
        markup_multiplier = 1 + (markup_percentage / 100)
        suggested_price = total_cost * markup_multiplier
        
        # Display cost breakdown and suggested price
        st.write("### Chi phí và Giá đề xuất")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"Chi phí nguyên liệu: **{total_material_cost:,.0f} VND**")
            st.write(f"Chi phí nhân công: **{production_fee:,.0f} VND**")
            st.write(f"Chi phí khác: **{other_fee:,.0f} VND**")
            st.write(f"Chi phí khấu hao tài sản: **{Depreciation_fee:,.0f} VND**")
            st.write(f"**Tổng chi phí: {total_cost:,.0f} VND**")
        with col2:
            st.write(f"Tỷ lệ lợi nhuận: **{markup_percentage:.2f}%**")
            st.write(f"Giá đề xuất: **{suggested_price:,.0f} VND**")
        
        # Allow user to use suggested price or enter a custom price
        use_suggested_price = st.checkbox("Sử dụng giá đề xuất", value=True, key="use_suggested_price")
        
        if use_suggested_price:
            new_product_price = int(suggested_price)
            st.write(f"Giá sản phẩm: **{new_product_price:,.0f} VND**")
        else:
            new_product_price = st.number_input("Giá tùy chỉnh", min_value=1000, value=int(suggested_price), step=1000, key="new_product_price")
        
        # Add product cost info for future reference
        product_cost_info = {
            'material_cost': total_material_cost,
            'production_fee': production_fee,
            'other_fee': other_fee,
            'total_cost': total_cost
        }
        
        if st.button("Thêm Sản phẩm"):
            if not new_product_id or not new_product_name or not new_product_category:
                st.error("Vui lòng điền đầy đủ thông tin sản phẩm")
            elif len(recipe_materials) == 0:
                st.error("Vui lòng thêm ít nhất một nguyên liệu vào công thức")
            elif new_product_id in st.session_state.products['product_id'].values:
                st.error(f"Mã sản phẩm {new_product_id} đã tồn tại")
            else:
                # Add new product
                new_product = pd.DataFrame({
                    'product_id': [new_product_id],
                    'name': [new_product_name],
                    'price': [new_product_price],
                    'category': [new_product_category],
                    'unit': [product_unit if selected_unit_option_product != "Khác" else product_unit]  # Add the unit field
                })
                
                st.session_state.products = pd.concat([st.session_state.products, new_product], ignore_index=True)
                
                # Add recipe
                recipe_rows = []
                for material in recipe_materials:
                    recipe_rows.append({
                        'product_id': new_product_id,
                        'material_id': material['material_id'],
                        'quantity': material['quantity']
                    })
                
                new_recipes = pd.DataFrame(recipe_rows)
                st.session_state.recipes = pd.concat([st.session_state.recipes, new_recipes], ignore_index=True)
                
                # Store cost info (optional, if you want to track this information)
                if 'product_costs' not in st.session_state:
                    st.session_state.product_costs = pd.DataFrame(columns=[
                        'product_id', 'material_cost', 'production_fee', 'other_fee', 'total_cost', 'price'
                    ])
                
                new_cost_info = pd.DataFrame({
                    'product_id': [new_product_id],
                    'material_cost': [total_material_cost],
                    'production_fee': [production_fee],
                    'other_fee': [other_fee],
                    'Depreciation_fee': [Depreciation_fee],  # Make sure this line is present with correct capitalization
                    'total_cost': [total_cost],
                    'price': [new_product_price]
                })

                st.session_state.product_costs = pd.concat([st.session_state.product_costs, new_cost_info], ignore_index=True)
                
                # Save products, recipes, and product costs data
                st.success(f"Sản phẩm {new_product_id} đã được thêm thành công!")
                save_dataframe(st.session_state.products, "products.csv")
                save_dataframe(st.session_state.recipes, "recipes.csv")
                if 'product_costs' in st.session_state:
                    save_dataframe(st.session_state.product_costs, "product_costs.csv")
    
    # Add new Delete Products tab
    with price_tab4:
        st.subheader("Xóa Sản phẩm")
        
        if not st.session_state.products.empty:
            # Create a list of options for the selectbox
            product_options = []
            for _, product in st.session_state.products.iterrows():
                product_options.append(f"{product['product_id']} - {product['name']}")
            
            selected_product = st.selectbox(
                "Chọn Sản phẩm để Xóa",
                options=product_options,
                key="delete_product_select"
            )
            
            if selected_product:
                # Extract product_id from the selection
                selected_product_id = selected_product.split(' - ')[0]
                
                # Find the product data
                product_data = st.session_state.products[st.session_state.products['product_id'] == selected_product_id]
                
                if not product_data.empty:
                    product_info = product_data.iloc[0]
                    
                    st.write(f"**Tên sản phẩm:** {product_info['name']}")
                    st.write(f"**Giá:** {product_info['price']:,.0f} VND")
                    st.write(f"**Phân loại:** {product_info['category']}")
                    
                    # Check if product is used in any order
                    product_in_orders = selected_product_id in st.session_state.order_items['product_id'].values
                    
                    if product_in_orders:
                        st.warning("Sản phẩm này đã được sử dụng trong các đơn hàng. Xóa sản phẩm có thể ảnh hưởng đến dữ liệu lịch sử.")
                    
                    # Delete confirmation
                    delete_confirmed = st.checkbox("Tôi hiểu rằng hành động này không thể hoàn tác", key="delete_confirm")
                    
                    if st.button("Xóa Sản phẩm") and delete_confirmed:
                        # Delete product from products DataFrame
                        st.session_state.products = st.session_state.products[st.session_state.products['product_id'] != selected_product_id]
                        
                        # Delete product's recipes from recipes DataFrame
                        st.session_state.recipes = st.session_state.recipes[st.session_state.recipes['product_id'] != selected_product_id]
                        
                        st.success(f"Sản phẩm {selected_product_id} đã được xóa thành công!")
        
                        # Save products and recipes data
                        save_dataframe(st.session_state.products, "products.csv")
                        save_dataframe(st.session_state.recipes, "recipes.csv")
        
        else:
            st.info("Chưa có dữ liệu sản phẩm để xóa.")

# Invoice Management Tab - Updated with Completion Status
elif tab_selection == "Quản lý Hóa đơn":
    st.header("Quản lý Hóa đơn")
    
    # Initialize invoice status tracking if not exists
    if 'invoice_status' not in st.session_state:
        st.session_state.invoice_status = pd.DataFrame(columns=[
            'invoice_id', 'is_completed', 'completion_date', 'notes'
        ])
    
    # Make sure all invoices have a status entry
    if not st.session_state.invoices.empty:
        for _, invoice in st.session_state.invoices.iterrows():
            invoice_id = invoice['invoice_id']
            if invoice_id not in st.session_state.invoice_status['invoice_id'].values:
                new_status = pd.DataFrame({
                    'invoice_id': [invoice_id],
                    'is_completed': [False],
                    'completion_date': [''],
                    'notes': [''],
                    'payment_status': ['Chưa thanh toán']  # Add default payment status
                })
                st.session_state.invoice_status = pd.concat([st.session_state.invoice_status, new_status], ignore_index=True)
            # Add payment_status column to existing records if it doesn't exist
            elif 'payment_status' not in st.session_state.invoice_status.columns:
                st.session_state.invoice_status['payment_status'] = 'Chưa thanh toán'
    
    invoice_tab1, invoice_tab2, invoice_tab3 = st.tabs(["Danh sách Hóa đơn", "Hóa đơn Chưa hoàn thành", "Xóa Hóa đơn"])
    
    # Phần code cập nhật với lựa chọn phương thức thanh toán
    with invoice_tab1:
        if len(st.session_state.invoices) > 0:
            st.subheader("Tất cả Hóa đơn")
            
            # Create a display version of the invoices with formatted values and status
            # Get the most up-to-date invoice status data before displaying
            invoices_with_status = st.session_state.invoices.merge(
                st.session_state.invoice_status[['invoice_id', 'is_completed', 'payment_status']],
                on='invoice_id',
                how='left'
            )
            
            # Fill NaN values from merge
            invoices_with_status['is_completed'] = invoices_with_status['is_completed'].fillna(False)
            invoices_with_status['payment_status'] = invoices_with_status['payment_status'].fillna("Chưa thanh toán")
            
            # Format for display
            display_invoices = pd.DataFrame({
                'ID Hóa đơn': invoices_with_status['invoice_id'],
                'Ngày': invoices_with_status['date'],
                'Khách hàng': invoices_with_status['customer_name'],
                'Tổng tiền': invoices_with_status['total_amount'].apply(lambda x: f"{x:,.0f} VND"),
                'Thanh toán': invoices_with_status['payment_method'],
                'Trạng thái': invoices_with_status['is_completed'].apply(
                    lambda x: "✅ Hoàn thành" if x else "⏳ Chưa hoàn thành"
                ),
                'Trạng thái TT': invoices_with_status['payment_status']
            })
            
            # Show the invoices sorted by date
            st.dataframe(display_invoices.sort_values('Ngày', ascending=False))
            
            # Filter options
            st.subheader("Lọc Hóa đơn")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                filter_status = st.radio(
                    "Trạng thái hoàn thành",
                    ["Tất cả", "Hoàn thành", "Chưa hoàn thành"],
                    key="invoice_status_filter"
                )
            
            with col2:
                # Get unique dates
                unique_dates = sorted(st.session_state.invoices['date'].unique(), reverse=True)
                filter_date = st.selectbox(
                    "Ngày",
                    ["Tất cả"] + unique_dates,
                    key="invoice_date_filter"
                )
            
            with col3:
                # Get payment methods - Use a standard set of payment methods for consistency
                standard_payment_methods = ["Tất cả", "Chuyển khoản", "Tiền mặt"]
                # Add any other unique methods found in the data that aren't in our standard list
                other_methods = [m for m in st.session_state.invoices['payment_method'].unique() 
                                if m not in standard_payment_methods and m != "Tất cả"]
                payment_methods = standard_payment_methods + other_methods
                filter_payment = st.selectbox(
                    "Phương thức thanh toán",
                    payment_methods,
                    key="invoice_payment_filter"
                )
            
            # Apply filters
            filtered_invoices = invoices_with_status.copy()
            
            if filter_status == "Hoàn thành":
                filtered_invoices = filtered_invoices[filtered_invoices['is_completed'] == True]
            elif filter_status == "Chưa hoàn thành":
                filtered_invoices = filtered_invoices[filtered_invoices['is_completed'] == False]
            
            if filter_date != "Tất cả":
                filtered_invoices = filtered_invoices[filtered_invoices['date'] == filter_date]
            
            if filter_payment != "Tất cả":
                filtered_invoices = filtered_invoices[filtered_invoices['payment_method'] == filter_payment]
            
            # Select invoice to view
            if not filtered_invoices.empty:
                invoice_options = []
                for _, invoice in filtered_invoices.iterrows():
                    status_emoji = "✅" if invoice['is_completed'] else "⏳"
                    payment_status_text = f" | {invoice['payment_status']}"
                    invoice_options.append(f"{invoice['invoice_id']} - {invoice['customer_name']} ({status_emoji}{payment_status_text})")
                
                selected_invoice = st.selectbox(
                    "Chọn Hóa đơn để Xem",
                    options=invoice_options,
                    key="view_invoice_select"
                )
                
                if selected_invoice:
                    # Extract invoice_id from the selection
                    selected_invoice_id = selected_invoice.split(' - ')[0]
                    
                    # Find the invoice data
                    invoice_data = st.session_state.invoices[st.session_state.invoices['invoice_id'] == selected_invoice_id]
                    status_data = st.session_state.invoice_status[st.session_state.invoice_status['invoice_id'] == selected_invoice_id]
                    
                    if not invoice_data.empty and not status_data.empty:
                        invoice_data = invoice_data.iloc[0]
                        status_data = status_data.iloc[0]
                        order_id = invoice_data['order_id']
                        
                        # Display invoice details
                        st.write("### Chi tiết Hóa đơn")
                        
                        # Invoice header in columns
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Hóa đơn #:** {selected_invoice_id}")
                            st.write(f"**Ngày:** {invoice_data['date']}")
                        with col2:
                            st.write(f"**Khách hàng:** {invoice_data['customer_name']}")
                            st.write(f"**Tổng tiền:** {invoice_data['total_amount']:,.0f} VND")
                        with col3:
                            st.write(f"**Thanh toán:** {invoice_data['payment_method']}")
                            status_text = "✅ Hoàn thành" if status_data['is_completed'] else "⏳ Chưa hoàn thành"
                            st.write(f"**Trạng thái:** {status_text}")
                            payment_status = status_data.get('payment_status', "Chưa thanh toán")
                            st.write(f"**Trạng thái TT:** {payment_status}")
                        
                        # Completion status toggle and notes
                        st.write("### Cập nhật Trạng thái")
                        completion_col1, completion_col2 = st.columns(2)
                        
                        with completion_col1:
                            new_status = st.checkbox(
                                "Đánh dấu đã hoàn thành",
                                value=status_data['is_completed'],
                                key=f"complete_{selected_invoice_id}"
                            )
                            
                            # Only show date input if completed
                            if new_status:
                                completion_date = status_data['completion_date']
                                if not completion_date:
                                    completion_date = datetime.date.today().strftime("%Y-%m-%d")
                                
                                new_completion_date = st.date_input(
                                    "Ngày hoàn thành",
                                    value=datetime.datetime.strptime(completion_date, "%Y-%m-%d").date() if completion_date else datetime.date.today(),
                                    key=f"completion_date_{selected_invoice_id}"
                                ).strftime("%Y-%m-%d")
                            else:
                                new_completion_date = ""

                            # Add payment method selector
                            payment_method_options = ["Chuyển khoản", "Tiền mặt"]
                            current_payment_method = invoice_data['payment_method']
                            # Set default index, if current method not in options, default to first option
                            default_payment_index = payment_method_options.index(current_payment_method) if current_payment_method in payment_method_options else 0
                            
                            new_payment_method = st.selectbox(
                                "Phương thức thanh toán",
                                options=payment_method_options,
                                index=default_payment_index,
                                key=f"payment_method_{selected_invoice_id}"
                            )

                            # Add payment status selector
                            payment_status_options = ["Chưa thanh toán", "Đã thanh toán một phần", "Đã thanh toán"]
                            current_payment_status = status_data.get('payment_status', "Chưa thanh toán")
                            new_payment_status = st.selectbox(
                                "Trạng thái thanh toán",
                                options=payment_status_options,
                                index=payment_status_options.index(current_payment_status) if current_payment_status in payment_status_options else 0,
                                key=f"payment_status_{selected_invoice_id}"
                            )

                        with completion_col2:
                            new_notes = st.text_area(
                                "Ghi chú",
                                value=status_data['notes'],
                                key=f"notes_{selected_invoice_id}"
                            )
                        
                        # Sửa đoạn code có lỗi, bỏ lệnh time.sleep()
                        if st.button("Lưu trạng thái", key=f"save_status_{selected_invoice_id}"):
                            status_idx = st.session_state.invoice_status[
                                st.session_state.invoice_status['invoice_id'] == selected_invoice_id
                            ].index[0]
                            
                            # Update status values
                            st.session_state.invoice_status.at[status_idx, 'is_completed'] = new_status
                            st.session_state.invoice_status.at[status_idx, 'completion_date'] = new_completion_date
                            st.session_state.invoice_status.at[status_idx, 'notes'] = new_notes
                            
                            # Add payment status update
                            if 'payment_status' not in st.session_state.invoice_status.columns:
                                st.session_state.invoice_status['payment_status'] = "Chưa thanh toán"
                            st.session_state.invoice_status.at[status_idx, 'payment_status'] = new_payment_status

                            # Update payment method in invoices dataframe
                            invoice_idx = st.session_state.invoices[
                                st.session_state.invoices['invoice_id'] == selected_invoice_id
                            ].index[0]
                            st.session_state.invoices.at[invoice_idx, 'payment_method'] = new_payment_method

                            # Save both invoice and status data
                            save_dataframe(st.session_state.invoice_status, "invoice_status.csv")
                            save_dataframe(st.session_state.invoices, "invoices.csv")
                            
                            st.success(f"Thông tin hóa đơn {selected_invoice_id} đã được cập nhật!")
                            # Bỏ dòng time.sleep(0.5) vì module time chưa được import
                            st.rerun()  # Force page rerun to refresh all components with new data
                                                
                        # Order items
                        st.write("### Các Mặt hàng")
                        order_items = st.session_state.order_items[st.session_state.order_items['order_id'] == order_id]
                        
                        if not order_items.empty:
                            # Get product names
                            order_items_with_names = order_items.copy()
                            if not st.session_state.products.empty:
                                order_items_with_names = order_items.merge(
                                    st.session_state.products[['product_id', 'name']],
                                    on='product_id',
                                    how='left'
                                )
                            
                            # Handle cases where products might be missing
                            if 'name' not in order_items_with_names.columns:
                                order_items_with_names['name'] = order_items_with_names['product_id'].apply(
                                    lambda pid: f"Sản phẩm {pid}"
                                )
                            
                            # Format for display
                            display_items = pd.DataFrame({
                                'Tên sản phẩm': order_items_with_names['name'],
                                'Số lượng': order_items_with_names['quantity'],
                                'Đơn giá': order_items_with_names['price'].apply(lambda x: f"{x:,.0f} VND"),
                                'Thành tiền': order_items_with_names['subtotal'].apply(lambda x: f"{x:,.0f} VND")
                            })
                            
                            # Display the items
                            st.dataframe(display_items)
                        else:
                            st.info("Không tìm thấy chi tiết đơn hàng.")
                        
                        # Invoice download link
                        st.subheader("Tải xuống Hóa đơn")
                        try:
                            pdf_data = generate_invoice_content(selected_invoice_id, order_id, as_pdf=True)
                            st.markdown(download_link(pdf_data, f"Hoadon_{selected_invoice_id}.pdf", "Tải Hóa đơn (PDF)", is_pdf=True), unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"Lỗi khi tạo hóa đơn: {str(e)}")
            else:
                st.info("Không có hóa đơn nào phù hợp với bộ lọc đã chọn.")
        else:
            st.info("Chưa có hóa đơn nào. Tạo đơn hàng để tạo hóa đơn.")
            
            # Add demo invoice button for testing
            if st.button("Tạo hóa đơn mẫu (Để kiểm tra)"):
                # Create a demo order and invoice
                order_id = f"ORD-DEMO-{uuid.uuid4().hex[:4].upper()}"
                invoice_id = f"INV-DEMO-{uuid.uuid4().hex[:4].upper()}"
                
                # Create order
                demo_order = pd.DataFrame({
                    'order_id': [order_id],
                    'date': [datetime.date.today().strftime("%Y-%m-%d")],
                    'customer_name': ["Khách hàng Mẫu"],
                    'customer_phone': ["0123456789"],
                    'total_amount': [150000],
                    'status': ['Hoàn thành']
                })
                
                # Create order items
                demo_item = pd.DataFrame({
                    'order_id': [order_id],
                    'product_id': ['P001'],
                    'quantity': [1],
                    'price': [150000],
                    'subtotal': [150000]
                })
                
                # Create invoice
                demo_invoice = pd.DataFrame({
                    'invoice_id': [invoice_id],
                    'order_id': [order_id],
                    'date': [datetime.date.today().strftime("%Y-%m-%d")],
                    'customer_name': ["Khách hàng Mẫu"],
                    'total_amount': [150000],
                    'payment_method': ['Tiền mặt']
                })
                
                # Create invoice status
                demo_status = pd.DataFrame({
                    'invoice_id': [invoice_id],
                    'is_completed': [False],
                    'completion_date': [''],
                    'notes': ['Hóa đơn mẫu để kiểm thử'],
                    'payment_status': ['Chưa thanh toán']
                })
                
                # Update session state
                st.session_state.orders = pd.concat([st.session_state.orders, demo_order], ignore_index=True)
                st.session_state.order_items = pd.concat([st.session_state.order_items, demo_item], ignore_index=True)
                st.session_state.invoices = pd.concat([st.session_state.invoices, demo_invoice], ignore_index=True)
                st.session_state.invoice_status = pd.concat([st.session_state.invoice_status, demo_status], ignore_index=True)
                
                # Save orders, order items, invoices, and invoice status data
                save_dataframe(st.session_state.orders, "orders.csv")
                save_dataframe(st.session_state.order_items, "order_items.csv")
                save_dataframe(st.session_state.invoices, "invoices.csv")
                save_dataframe(st.session_state.invoice_status, "invoice_status.csv")
                
                st.success("Đã tạo hóa đơn mẫu thành công!")
                time.sleep(0.5)  # Brief pause to ensure data is saved
                st.rerun()  # Force page rerun
    
    with invoice_tab2:
        st.subheader("Hóa đơn Chưa hoàn thành")
        
        # Get incomplete invoices
        if not st.session_state.invoices.empty and not st.session_state.invoice_status.empty:
            incomplete_status = st.session_state.invoice_status[st.session_state.invoice_status['is_completed'] == False]
            
            if not incomplete_status.empty:
                incomplete_invoices = st.session_state.invoices.merge(
                    incomplete_status[['invoice_id']],
                    on='invoice_id',
                    how='inner'
                )
                
                if not incomplete_invoices.empty:
                    # Format for display
                    display_incomplete = pd.DataFrame({
                        'ID Hóa đơn': incomplete_invoices['invoice_id'],
                        'Ngày': incomplete_invoices['date'],
                        'Khách hàng': incomplete_invoices['customer_name'],
                        'Tổng tiền': incomplete_invoices['total_amount'].apply(lambda x: f"{x:,.0f} VND"),
                        'Thanh toán': incomplete_invoices['payment_method']
                    })
                    
                    # Show the incomplete invoices
                    st.dataframe(display_incomplete.sort_values('Ngày', ascending=False))
                    
                    # Quick completion tools
                    st.subheader("Hoàn thành Nhanh")
                    
                    incomplete_options = []
                    for _, invoice in incomplete_invoices.iterrows():
                        incomplete_options.append(f"{invoice['invoice_id']} - {invoice['customer_name']}")
                    
                    selected_to_complete = st.multiselect(
                        "Chọn hóa đơn để đánh dấu hoàn thành",
                        options=incomplete_options,
                        key="batch_complete_select"
                    )
                    
                    if selected_to_complete:
                        if st.button("Đánh dấu đã hoàn thành", key="batch_complete_button"):
                            completion_date = datetime.date.today().strftime("%Y-%m-%d")
                            completion_note = "Đánh dấu hoàn thành theo lô"
                            
                            for invoice_string in selected_to_complete:
                                invoice_id = invoice_string.split(' - ')[0]
                                
                                # Find status entry
                                status_idxs = st.session_state.invoice_status[
                                    st.session_state.invoice_status['invoice_id'] == invoice_id
                                ].index
                                
                                if not status_idxs.empty:
                                    status_idx = status_idxs[0]
                                    
                                    # Update status
                                    st.session_state.invoice_status.at[status_idx, 'is_completed'] = True
                                    st.session_state.invoice_status.at[status_idx, 'completion_date'] = completion_date
                                    
                                    # Only update notes if empty
                                    if not st.session_state.invoice_status.at[status_idx, 'notes']:
                                        st.session_state.invoice_status.at[status_idx, 'notes'] = completion_note
                            
                            st.success(f"Đã cập nhật {len(selected_to_complete)} hóa đơn!")
                            # Save invoice status data
                            save_dataframe(st.session_state.invoice_status, "invoice_status.csv")
                            
                            st.rerun()  # Changed from experimental_rerun to rerun
                else:
                    st.info("Không có hóa đơn nào chưa hoàn thành.")
            else:
                st.info("Không có hóa đơn nào chưa hoàn thành.")
        else:
            st.info("Chưa có hóa đơn nào để hiển thị.")
    
    with invoice_tab3:
        st.subheader("Xóa Hóa đơn")
        
        if len(st.session_state.invoices) > 0:
            # Tạo danh sách các hóa đơn
            invoice_options = []
            for _, invoice in st.session_state.invoices.iterrows():
                # Lấy thông tin trạng thái nếu có
                status = "⚠️ Không xác định"
                if 'invoice_status' in st.session_state and not st.session_state.invoice_status.empty:
                    status_data = st.session_state.invoice_status[
                        st.session_state.invoice_status['invoice_id'] == invoice['invoice_id']
                    ]
                    if not status_data.empty:
                        is_completed = status_data['is_completed'].iloc[0]
                        status = "✅ Hoàn thành" if is_completed else "⏳ Chưa hoàn thành"
                
                invoice_options.append(f"{invoice['invoice_id']} - {invoice['date']} - {invoice['customer_name']} ({status})")
            
            # Chọn hóa đơn để xóa
            selected_invoice_to_delete = st.selectbox(
                "Chọn Hóa đơn để Xóa",
                options=invoice_options,
                key="delete_invoice_select"
            )
            
            if selected_invoice_to_delete:
                # Trích xuất invoice_id từ lựa chọn
                selected_invoice_id = selected_invoice_to_delete.split(' - ')[0]
                
                # Tìm dữ liệu hóa đơn
                invoice_data = st.session_state.invoices[st.session_state.invoices['invoice_id'] == selected_invoice_id]
                
                if not invoice_data.empty:
                    invoice_info = invoice_data.iloc[0]
                    
                    # Hiển thị thông tin hóa đơn
                    st.write("### Thông tin Hóa đơn")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Mã Hóa đơn:** {invoice_info['invoice_id']}")
                        st.write(f"**Ngày:** {invoice_info['date']}")
                        st.write(f"**Khách hàng:** {invoice_info['customer_name']}")
                    with col2:
                        st.write(f"**Tổng tiền:** {invoice_info['total_amount']:,.0f} VND")
                        st.write(f"**Phương thức thanh toán:** {invoice_info['payment_method']}")
                        
                        # Hiển thị thông tin liên quan (đơn hàng)
                        order_id = invoice_info['order_id']
                        st.write(f"**Mã Đơn hàng:** {order_id}")
                    
                    # Kiểm tra trạng thái hoàn thành
                    is_completed = False
                    if 'invoice_status' in st.session_state and not st.session_state.invoice_status.empty:
                        status_data = st.session_state.invoice_status[
                            st.session_state.invoice_status['invoice_id'] == selected_invoice_id
                        ]
                        if not status_data.empty:
                            is_completed = status_data['is_completed'].iloc[0]
                    
                    # Cảnh báo dựa trên trạng thái
                    if is_completed:
                        st.warning("Hóa đơn này đã được đánh dấu là Hoàn thành. Bạn có chắc chắn muốn xóa không?")
                    else:
                        st.info("Hóa đơn này Chưa hoàn thành và có thể xóa an toàn.")
                    
                    # Xác nhận xóa
                    delete_confirmed = st.checkbox("Tôi hiểu rằng hành động này không thể hoàn tác", key="delete_invoice_confirm")
                    
                    # Option to delete related order
                    delete_order_too = st.checkbox("Xóa cả Đơn hàng liên quan", value=False, key="delete_order_too")
                    
                    if st.button("Xóa Hóa đơn", key="confirm_delete_invoice"):
                        if delete_confirmed:
                            # 0. Điều chỉnh doanh thu và hoàn lại nguyên liệu trước khi xóa các đối tượng
                            success = adjust_income_after_delete_invoice(selected_invoice_id, order_id)
                            if success and show_debug:
                                st.sidebar.success("Đã điều chỉnh doanh thu và hoàn lại nguyên liệu thành công")
                            
                            # 1. Xóa thông tin trạng thái hóa đơn
                            if 'invoice_status' in st.session_state and not st.session_state.invoice_status.empty:
                                st.session_state.invoice_status = st.session_state.invoice_status[
                                    st.session_state.invoice_status['invoice_id'] != selected_invoice_id
                                ]
                            
                            # 2. Xóa hóa đơn
                            st.session_state.invoices = st.session_state.invoices[
                                st.session_state.invoices['invoice_id'] != selected_invoice_id
                            ]
                            
                            # 3. Nếu được chọn, xóa đơn hàng liên quan
                            if delete_order_too:
                                # Xóa đơn hàng và các chi tiết đơn hàng
                                st.session_state.orders = st.session_state.orders[
                                    st.session_state.orders['order_id'] != order_id
                                ]
                                
                                st.session_state.order_items = st.session_state.order_items[
                                    st.session_state.order_items['order_id'] != order_id
                                ]
                            
                            # 4. Lưu các thay đổi
                            save_dataframe(st.session_state.invoices, "invoices.csv")
                            save_dataframe(st.session_state.invoice_status, "invoice_status.csv")
                            save_dataframe(st.session_state.income, "income.csv")
                            save_dataframe(st.session_state.materials, "materials.csv")
                            
                            if delete_order_too:
                                save_dataframe(st.session_state.orders, "orders.csv")
                                save_dataframe(st.session_state.order_items, "order_items.csv")
                            
                            st.success(f"Đã xóa hóa đơn {selected_invoice_id} thành công!" + 
                                    (f" và đơn hàng {order_id}" if delete_order_too else ""))
                            
                            # Làm mới trang
                            st.rerun()
                        else:
                            st.error("Vui lòng xác nhận bằng cách đánh dấu vào ô xác nhận trước khi xóa.")

# Data Management and Debug Tab
elif tab_selection == "Quản lý Dữ liệu":
    st.header("Quản lý Dữ liệu")
    
    data_tab1, data_tab2, data_tab3 = st.tabs(["Sao lưu & Phục hồi", "Xóa Dữ liệu", "Thông tin Dữ liệu"])
    
    with data_tab1:
        st.subheader("Sao lưu & Phục hồi Dữ liệu")
        
        # Add backup/restore UI
        add_backup_restore_ui()
        
        # Display MongoDB storage information if available
        if "mongo_client" in st.session_state and "mongo_db" in st.session_state:
            st.subheader("Thông tin Lưu trữ MongoDB")
            try:
                mongo_client = st.session_state.mongo_client
                mongo_db = st.session_state.mongo_db
                
                # Get database information
                db_name = mongo_db.name
                
                # Define expected collection names (matching CSV file names used in the app)
                expected_collections = [
                    "products", "materials", "recipes", "orders", 
                    "order_items", "invoices", "invoice_status", 
                    "income", "material_costs"
                ]
                
                # Get actual collection names from MongoDB
                actual_collections = mongo_db.list_collection_names()
                
                # Get collection statistics
                collections_info = []
                for collection_name in expected_collections:
                    # Check if collection exists
                    exists = collection_name in actual_collections
                    doc_count = mongo_db[collection_name].count_documents({}) if exists else 0
                    
                    collections_info.append({
                        "Tên bảng": collection_name,
                        "Tồn tại": "✓" if exists else "✗",
                        "Số bản ghi": doc_count
                    })
                
                st.info(f"Dữ liệu đang được lưu trữ trong MongoDB Atlas: {db_name}")
                st.write("#### Các bảng trong MongoDB:")
                st.table(pd.DataFrame(collections_info))
                
                # Show warning if any expected collection is missing
                missing_collections = [c for c in expected_collections if c not in actual_collections]
                if missing_collections:
                    st.warning(f"Một số bảng chưa được tạo trong MongoDB: {', '.join(missing_collections)}. Các bảng sẽ được tạo tự động khi lưu dữ liệu.")
                
            except Exception as e:
                st.error(f"Lỗi khi truy cập MongoDB: {str(e)}")
        else:
            st.info("Đang sử dụng lưu trữ phiên (session) cho dữ liệu. Lưu ý rằng dữ liệu có thể bị mất khi làm mới trang.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Lưu Tất cả Dữ liệu"):
                try:
                    # Save all current data
                    save_all_data()
                    st.success("Đã lưu tất cả dữ liệu thành công!")
                except Exception as e:
                    st.error(f"Lỗi khi lưu dữ liệu: {str(e)}")
        
        with col2:
            if st.button("Tải lại Dữ liệu"):
                try:
                    # Force reload all data from storage
                    st.session_state.products = load_dataframe("products.csv", default_products)
                    st.session_state.materials = load_dataframe("materials.csv", default_materials)
                    st.session_state.recipes = load_dataframe("recipes.csv", default_recipes)
                    st.session_state.orders = load_dataframe("orders.csv", default_orders)
                    st.session_state.order_items = load_dataframe("order_items.csv", default_order_items)
                    st.session_state.invoices = load_dataframe("invoices.csv", default_invoices)
                    st.session_state.income = load_dataframe("income.csv", default_income)
                    st.session_state.material_costs = load_dataframe("material_costs.csv", default_material_costs)
                    st.session_state.invoice_status = load_dataframe("invoice_status.csv", default_invoice_status)
                    
                    st.success("Đã tải lại dữ liệu thành công!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi khi tải lại dữ liệu: {str(e)}")

    with data_tab2:
        st.subheader("Xóa Dữ liệu")
        st.warning("⚠️ **Cảnh báo**: Các hành động ở đây có thể làm mất dữ liệu vĩnh viễn!")
        
        reset_options = st.radio(
            "Chọn loại dữ liệu để xóa:",
            ["Không xóa gì", "Xóa dữ liệu đơn hàng và hóa đơn", "Xóa dữ liệu kho", "Xóa dữ liệu sản phẩm", "Xóa tất cả dữ liệu"]
        )
        
        if reset_options != "Không xóa gì":
            st.write(f"**Bạn đã chọn:** {reset_options}")
            
            # Display what will be deleted
            if reset_options == "Xóa dữ liệu đơn hàng và hóa đơn":
                st.write("Các dữ liệu sau sẽ bị xóa:")
                st.write("- Đơn hàng")
                st.write("- Chi tiết đơn hàng")
                st.write("- Hóa đơn")
                st.write("- Trạng thái hóa đơn")
                st.write("- Doanh thu")
            elif reset_options == "Xóa dữ liệu kho":
                st.write("Các dữ liệu sau sẽ bị xóa:")
                st.write("- Nguyên liệu (sẽ được thiết lập lại về mặc định)")
                st.write("- Chi phí nguyên liệu")
            elif reset_options == "Xóa dữ liệu sản phẩm":
                st.write("Các dữ liệu sau sẽ bị xóa:")
                st.write("- Sản phẩm (sẽ được thiết lập lại về mặc định)")
                st.write("- Công thức (sẽ được thiết lập lại về mặc định)")
            else:  # Xóa tất cả
                st.write("**Tất cả dữ liệu** sẽ bị xóa và thiết lập lại về mặc định!")
            
            # Multiple confirmations for safety
            confirm1 = st.checkbox("Tôi muốn xóa dữ liệu đã chọn", key="confirm_delete_1")
            confirm2 = st.checkbox("Tôi hiểu rằng dữ liệu bị xóa sẽ không thể khôi phục (trừ khi có bản sao lưu)", key="confirm_delete_2")
            
            delete_password = st.text_input("Nhập 'XOA' để xác nhận:", type="password", key="delete_password")
            
            if st.button("Xóa Dữ liệu") and confirm1 and confirm2 and delete_password == "XOA":
                try:               
                    if reset_options == "Xóa dữ liệu đơn hàng và hóa đơn":
                        # Reset order-related data
                        st.session_state.orders = default_orders.copy()
                        st.session_state.order_items = default_order_items.copy()
                        st.session_state.invoices = default_invoices.copy()
                        st.session_state.invoice_status = default_invoice_status.copy()
                        st.session_state.income = default_income.copy()
                        
                        # Save the reset data
                        save_dataframe(st.session_state.orders, "orders.csv")
                        save_dataframe(st.session_state.order_items, "order_items.csv")
                        save_dataframe(st.session_state.invoices, "invoices.csv")
                        save_dataframe(st.session_state.invoice_status, "invoice_status.csv")
                        save_dataframe(st.session_state.income, "income.csv")
                        
                    elif reset_options == "Xóa dữ liệu kho":
                        # Reset materials data
                        st.session_state.materials = default_materials.copy()
                        st.session_state.material_costs = default_material_costs.copy()
                        
                        # Save the reset data
                        save_dataframe(st.session_state.materials, "materials.csv")
                        save_dataframe(st.session_state.material_costs, "material_costs.csv")
                        
                    elif reset_options == "Xóa dữ liệu sản phẩm":
                        # Reset product data
                        st.session_state.products = default_products.copy()
                        st.session_state.recipes = default_recipes.copy()
                        
                        # Save the reset data
                        save_dataframe(st.session_state.products, "products.csv")
                        save_dataframe(st.session_state.recipes, "recipes.csv")
                        
                    else:  # Xóa tất cả
                        # Reset all data
                        st.session_state.products = default_products.copy()
                        st.session_state.materials = default_materials.copy()
                        st.session_state.recipes = default_recipes.copy()
                        st.session_state.orders = default_orders.copy()
                        st.session_state.order_items = default_order_items.copy()
                        st.session_state.invoices = default_invoices.copy()
                        st.session_state.invoice_status = default_invoice_status.copy()
                        st.session_state.income = default_income.copy()
                        st.session_state.material_costs = default_material_costs.copy()
                        
                        # Save all reset data
                        save_all_data()
                    
                    st.success(f"Đã xóa dữ liệu thành công! Có thể tải bản sao lưu từ tab 'Sao lưu & Phục hồi'")
                    st.info("Ứng dụng sẽ tải lại sau 5 giây...")
                    import time
                    time.sleep(5)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Lỗi khi xóa dữ liệu: {str(e)}")
    
    with data_tab3:
        st.subheader("Thông tin Dữ liệu")
        
        # Show session state data sizes
        st.subheader("Dữ liệu trong phiên hiện tại")
        
        # Create table of all data structures in app
        session_data = []
        for key in [
            'products', 'materials', 'recipes', 'orders', 'order_items', 
            'invoices', 'income', 'material_costs', 'invoice_status'
        ]:
            if key in st.session_state:
                rows = len(st.session_state[key])
                columns = len(st.session_state[key].columns) if rows > 0 else 0
                
                # Calculate memory usage
                memory_usage = 0
                if rows > 0:
                    memory_usage = st.session_state[key].memory_usage(deep=True).sum()
                
                session_data.append({
                    "Tên dữ liệu": key,
                    "Số dòng": rows,
                    "Số cột": columns,
                    "Bộ nhớ (bytes)": f"{memory_usage:,.0f}" if memory_usage > 0 else "0"
                })
        
        st.table(pd.DataFrame(session_data))
        
        # MongoDB storage info
        if "mongo_client" in st.session_state and "mongo_db" in st.session_state:
            st.subheader("Tình trạng MongoDB")
            
            try:
                mongo_client = st.session_state.mongo_client
                mongo_db = st.session_state.mongo_db
                
                # Define expected collections (same as app data structures)
                expected_collections = [
                    "products", "materials", "recipes", "orders", 
                    "order_items", "invoices", "invoice_status", 
                    "income", "material_costs"
                ]
                
                # Get status information
                actual_collections = mongo_db.list_collection_names()
                
                # Compare app data with MongoDB data
                comparison_data = []
                for key in expected_collections:
                    # Check if collection exists in MongoDB
                    exists_in_mongo = key in actual_collections
                    mongo_count = mongo_db[key].count_documents({}) if exists_in_mongo else 0
                    
                    # Check if data exists in session state
                    exists_in_session = key in st.session_state
                    session_count = len(st.session_state[key]) if exists_in_session else 0
                    
                    # Check if counts match
                    status = "✓ Đồng bộ" if mongo_count == session_count else "⚠️ Khác biệt"
                    
                    comparison_data.append({
                        "Tên dữ liệu": key,
                        "MongoDB (số bản ghi)": mongo_count,
                        "Session (số dòng)": session_count,
                        "Trạng thái": status
                    })
                
                st.write("#### So sánh dữ liệu MongoDB và Phiên hiện tại:")
                st.table(pd.DataFrame(comparison_data))
                
                # Show warning if any data is out of sync
                out_of_sync = [item["Tên dữ liệu"] for item in comparison_data if item["Trạng thái"] != "✓ Đồng bộ"]
                if out_of_sync:
                    st.warning(f"Dữ liệu không đồng bộ: {', '.join(out_of_sync)}. Hãy sử dụng nút 'Lưu Tất cả Dữ liệu' để cập nhật MongoDB.")
                
            except Exception as e:
                st.error(f"Lỗi khi truy cập MongoDB: {str(e)}")
        
        # Add a force save button
        if st.button("Lưu lại tất cả dữ liệu"):
            save_all_data()
            st.success("Đã lưu lại tất cả dữ liệu thành công!")