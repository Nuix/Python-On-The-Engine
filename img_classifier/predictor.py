"""
Author: Steven Luke (steven.luke@nuix.com)
Date: 2022.04.04
Python Version: 3.9

Summary: Implements an image classification predictor based on the ResNet50 model and the ImageNet training.

Description:
This is a simple, single-method implementation of an image classifier.  It uses a pre-made and open source model along
with open source pre-trained weights, so the results will not be particularly good or appropriate for real-world use
cases.  It is just meant as a sample use case.

This is designed to be part of either a Command Line application (using the cli.predict_from_folder module) or
Microservice application (using the microservice.predict_service module).  It does nothing on its own.

"""
from keras.preprocessing.image import img_to_array
from tensorflow.keras.applications.resnet50 import preprocess_input
from tensorflow.keras.applications.resnet50 import decode_predictions
from tensorflow.keras.applications.resnet50 import ResNet50

MODEL_IMG_SIZE = 224  # in pixels
model = ResNet50(weights='imagenet')


def predict(get_images):
    """
    Make predictions on a list of images and return the labels and probabilities for the top 3 most likely
    classifications.

    This function uses an unmodified version of the ResNet50 model.  It is not intended for real use in a case, it is
    simply a demonstration of some work that would need to be done in an external Python application.

    The results are passed back as a list of tuples - each tuple containing the text label of prediction in position
    0, and the probability score in position 1.

    Images will be processed one at a time.

    :param get_images: This is a callback to get the images to make predictions for.  It should return a list of the
                       images as pillow images, but with no other pre-processing done.  Images should be RGB - and
                       should be shaped as [columns, rows, 3] with the 3 channels in RGB.
                       It would be nice of the implementer make get_images a generator that yields one image at a time
                       instead of making it return all images to be memory-friendly.
    :return: A list of results.  Each result is a tuple of up to 3 items, each item being the label and score:
             [..., ( (<label1>, <score1>), (<label2>, <score2>), (<label3>, <score3>) ), ...].  The length of the list
             matches the number of images returned from the get_images method. If there was an error processing an image
             that image's results will instead be a tuple with the word "ERROR" in the 0th position, and the exception
             in the second position: [..., ('ERROR', <ImproperShapeException...>), ...]
    """

    predictions = []
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
