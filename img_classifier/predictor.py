from keras.preprocessing.image import img_to_array
from tensorflow.keras.applications.resnet50 import preprocess_input
from tensorflow.keras.applications.resnet50 import decode_predictions
from tensorflow.keras.applications.resnet50 import ResNet50

MODEL_IMG_SIZE = 224  # in pixels


def predict(get_images):
    """
    Make predictions on a list of images and return the label and their probability and get the top 3 most likely
    classifications.

    This function uses an unmodified version of the VGG16 model from the Oxford Visual Geometry Group.  It is not
    intended for real use in a case, it is simply a demonstration of what could be used.

    The results are passed back as a list of tuples - each tuple containing the text label of prediction in position
    0, and the probability score in position 1.

    Images will be processed one at a time.

    :param get_images: This is a callback to get the images to make predictions for.  It should return a list of the
                       images as numpy arrays, but with no other pre-processing done.  Images should be in the format
                       as read from skimage.io.imread - that is shaped as [rows, columns, 3] with the 3 channels in RGB.
                       It would be nice of the implementer make get_images a generator that yields one image at a time
                       instead of making it return all images to be memory-friendly.
    :return: A list of results.  Each result is a tuple of up to 3 items, each item being the label and score:
             [( (<label1>, <score1>), (<label2>, <score2>), (<label3>, <score3>))].  The length of the list matches
             the number of images returned from the get_images method.
    """

    predictions = []
    model = ResNet50(weights='imagenet')
    index = 0
    for img_pixels in get_images():
        # Resize to required images for the model
        img_pixels = img_pixels.resize((MODEL_IMG_SIZE, MODEL_IMG_SIZE))
        img_array = img_to_array(img_pixels)
        img_array = img_array.reshape((1, img_array.shape[0], img_array.shape[1], img_array.shape[2]))

        results = []
        try:
            img_array = preprocess_input(img_array)

            # Predict
            inference = model.predict(img_array)
            labels = decode_predictions(inference, top=3)[0]  # Analyzing one image, so just look at first row

            for label in labels:
                results.append((label[1], label[2]))
            predictions.append(tuple(results))
        except Exception as e:
            print(f"Error in image: {index}")
            print(f"Error: {e}")
            predictions.append(('ERROR', e))
        finally:
            index += 1

    # Return the predictions
    return predictions
