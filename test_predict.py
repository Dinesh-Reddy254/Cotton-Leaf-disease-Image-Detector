import os

# Change to project directory
os.chdir(r'C:/Users/Admin/OneDrive/Desktop/Projects/cotton-disease-detection')

# Import app and db
import app
from db_models import db, User, APIKey

# Ensure tables exist
app.app.app_context().push()
db.create_all()

# Create a test user if not exists
user = User.query.filter_by(username='testuser').first()
if not user:
    user = User(username='testuser', email='test@example.com')
    user.set_password('Passw0rd!')
    db.session.add(user)
    db.session.commit()

# Create an API key for the user
api_key_obj = APIKey.query.filter_by(user_id=user.id).first()
if not api_key_obj:
    api_key_obj = APIKey(user_id=user.id, key=APIKey.generate_key(), name='testkey')
    db.session.add(api_key_obj)
    db.session.commit()
key = api_key_obj.key

# Generate a dummy image (green 224x224) and save it
from PIL import Image
img = Image.new('RGB', (224, 224), color='green')
img_path = 'test_image.jpg'
img.save(img_path, format='JPEG')

# Use Flask test client to call the prediction endpoint
client = app.app.test_client()
with open(img_path, 'rb') as f:
    data = {'file': (f, img_path)}
    resp = client.post('/api/v1/predict', data=data, headers={'X-API-Key': key})
    print('Status:', resp.status_code)
    print('JSON:', resp.get_json())
