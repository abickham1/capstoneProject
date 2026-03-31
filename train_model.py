import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

AUTOTUNE = tf.data.AUTOTUNE
image_size = (160, 160)
batch_size = 25


# Load datasets
train_dataset = tf.keras.utils.image_dataset_from_directory(
    "data/seed",
    image_size= image_size,
    batch_size= batch_size
)

val_dataset = tf.keras.utils.image_dataset_from_directory(
    "data/validation",
    image_size= image_size,
    batch_size= batch_size
)

data_augmentation = tf.keras.Sequential([
    layers.RandomFlip("horizontal_and_vertical"),
    layers.RandomRotation(0.2),
    layers.RandomZoom(0.2),
])

base_model = MobileNetV2(
    input_shape=(160, 160, 3), 
    include_top=False, 
    weights='imagenet'
)
base_model.trainable = False

model = models.Sequential([
    data_augmentation,
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.Dense(128, activation='relu'),
    layers.Dropout(0.5),
    layers.Dense(10, activation='softmax')
])

def preprocess(image, label):
    image = preprocess_input(image)
    return image, label 

train_dataset = train_dataset.map(preprocess, num_parallel_calls = AUTOTUNE)
val_dataset = val_dataset.map(preprocess, num_parallel_calls = AUTOTUNE)

train_dataset = train_dataset.prefetch(buffer_size=AUTOTUNE)
val_dataset = val_dataset.prefetch(buffer_size=AUTOTUNE)

model.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

history = model.fit(
    train_dataset,
    validation_data=val_dataset,
    epochs= 10
)


loss, accuracy = model.evaluate(val_dataset)
print("Validation accuracy:", accuracy)

model.save("galaxy_classifier.keras")