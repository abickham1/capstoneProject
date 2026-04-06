import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.applications.efficientnet import preprocess_input
import os
import numpy as np

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

AUTOTUNE = tf.data.AUTOTUNE
image_size = (224, 224) 
batch_size = 8

train_dataset = tf.keras.utils.image_dataset_from_directory(
    "data/seed",
    image_size=image_size,
    batch_size=batch_size
)

val_dataset = tf.keras.utils.image_dataset_from_directory(
    "data/validation",
    image_size=image_size,
    batch_size=batch_size
)

data_augmentation = tf.keras.Sequential([
    layers.RandomFlip("horizontal"),
    layers.RandomRotation(0.05),
    layers.RandomZoom(0.05),
])

base_model = EfficientNetB0(
    input_shape=(224, 224, 3),
    include_top=False,
    weights='imagenet'
)

base_model.trainable = False

num_classes = len(train_dataset.class_names)

model = models.Sequential([
    data_augmentation,
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.Dense(128, activation='relu', kernel_regularizer=tf.keras.regularizers.l2(0.001)),
    layers.BatchNormalization(),
    layers.Dropout(0.5),
    layers.Dense(num_classes, activation='softmax')
])

def preprocess(image, label):
    return preprocess_input(image), label

train_dataset = train_dataset.map(preprocess, num_parallel_calls=AUTOTUNE)
val_dataset = val_dataset.map(preprocess, num_parallel_calls=AUTOTUNE)

train_dataset = train_dataset.cache().shuffle(1000).prefetch(AUTOTUNE)
val_dataset = val_dataset.cache().prefetch(AUTOTUNE)

early_stop = tf.keras.callbacks.EarlyStopping(
    monitor='val_accuracy',
    patience=2,
    restore_best_weights=True
)

checkpoint = tf.keras.callbacks.ModelCheckpoint(
    "best_efficientnet.keras",
    monitor="val_accuracy",
    save_best_only=True,
    verbose=1
)

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=3e-5),
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

history = model.fit(
    train_dataset,
    validation_data=val_dataset,
    epochs= 10,
    callbacks=[early_stop, checkpoint]
)
#load the best model and evaluate on validation set
model = tf.keras.models.load_model("best_efficientnet.keras")

def tta_predict(model, dataset, n=5):
    preds = []

    for _ in range(n):
        batch_preds = []
        for x, _ in dataset:
            x_aug = tf.image.random_flip_left_right(x)
            x_aug = tf.image.random_flip_up_down(x_aug)

            p = model.predict(x_aug, verbose=0)
            batch_preds.append(p)
        preds.append(np.concatenate(batch_preds, axis=0))

    return np.mean(preds, axis=0)


#run TTA prediction on validation set
tta_predictions = tta_predict(model, val_dataset)
y_true = np.concatenate([y for _, y in val_dataset], axis=0)
y_pred = np.argmax(tta_predictions, axis=1)

tta_accuracy = np.mean(y_true == y_pred)
print("Validation accuracy with TTA:", tta_accuracy)

loss, accuracy = model.evaluate(val_dataset)
print("Validation accuracy:", accuracy)

model.save("final_galaxy_classifier.keras")