# Utility functions to be used elsewhere if needed

from PIL import Image, ImageOps, ImageFilter
import numpy
import copy

class Util:

    @staticmethod
    def ConvertToList(image2DArray):
        imageList = []
        for eachRow in image2DArray:
            for eachBit in eachRow:
                imageList.append(eachBit)
        return imageList

    @staticmethod
    def ArrayToImg(image2DArray, saveAs="Processed.png"):
        image2DArray = (image2DArray * 255).astype(numpy.uint8)
        img = Image.fromarray(image2DArray, "L")
        inverted_image = ImageOps.invert(img)
        inverted_image.save(saveAs)

    @staticmethod
    def ConvertArrayToImg(imgArray):
        image2DArray = (imgArray * 255).astype(numpy.uint8)
        img = Image.fromarray(image2DArray, "L")
        inverted_image = ImageOps.invert(img)
        return inverted_image

    @staticmethod
    def RotateImage(filePath, degree):
        im = Image.open(filePath)
        im.rotate(45).save("Processed.png")
    
    # @staticmethod
    # def GetDiff( imgA, imgB):
    #     return abs(imgA - imgB)

    @staticmethod
    def GetDiff(imgArrayA, imgArrayB):
        diffMatrix =  abs(numpy.array(imgArrayA) - numpy.array(imgArrayB))
        return numpy.count_nonzero(diffMatrix)

        # diffPixelCount = 0

        # # Get the diff pixel count using nditer
        # for pixel in numpy.nditer(diffMatrix):
        #     if pixel != 0: diffPixelCount+=1
        # return diffPixelCount

    @staticmethod
    def GetBlackPixelCount(imgArray):
        return numpy.count_nonzero(imgArray)

        # count = 0
        # for pixel in numpy.nditer(imgArray):
        #     if pixel != 0: count+=1
        # return count

    @staticmethod
    def PrintImgComponents(imgCompArray):
        components = []
        for pixel in numpy.nditer(imgCompArray):
            if pixel != 0 and pixel not in components: components.append(pixel)
        num = 0
        for comp in components:
            tempArray = copy.deepcopy(imgCompArray)
            tempArray[tempArray != comp] = 0 # Mask other components
            tempArray[tempArray == comp] = 1 # Make the current component 1 (pure black)
            Util.ArrayToImg(tempArray,str(num) + "_component.png")
            num+=1

    # Returns an array of different img component arrays of an image. Also indicates
    # which one is on the left, and which one is on the right. 
    # ONLY WORKS (CORRECTLY) FOR IMAGES WITH 2 COMPONENTS
    @staticmethod
    def GetSeparateComponents(imgCompArray):
        components = []
        tempReturnArray = [] 
        returnArray = []
        for pixel in numpy.nditer(imgCompArray):
            if pixel != 0 and pixel not in components: components.append(pixel)
        print("Components: ", components)
        for comp in components:
            tempArray = copy.deepcopy(imgCompArray)
            tempArray[tempArray != comp] = 0 # Mask other components
            tempArray[tempArray == comp] = 1 # Make the current component 1 (pure black)
            tempReturnArray.append(tempArray)

        comp1_leftMost = numpy.transpose(numpy.nonzero(tempReturnArray[0]))[0]
        comp2_leftMost = numpy.transpose(numpy.nonzero(tempReturnArray[1]))[0]

        # If the order is already correct, return it
        if (comp1_leftMost[1] <= comp2_leftMost[1]):
            return tempReturnArray
        # If not, re-arrange, then return
        else:
            returnArray.append(tempReturnArray[1])
            returnArray.append(tempReturnArray[0])
            return returnArray

        # print("Component 0 left most: ", numpy.transpose(numpy.nonzero(returnArray[0]))[0])
        # print("Component 1 left most: ", numpy.transpose(numpy.nonzero(returnArray[1]))[0])
        # return returnArray

    @staticmethod
    def MoveLRByOffset(imgArray, offset):
        indices = numpy.transpose(numpy.nonzero(imgArray))
        print("indices: ", indices)
        return numpy.roll(imgArray,offset)

    @staticmethod
    def GetTransposedImgArray(imgArray, transposeMethod):
        MASK_VALUE = 7 # arbitrary value to convert black pixels to
        BLACK_PIXEL_THRESHOLD = 10
        nonNumberTransposes = [Image.FLIP_LEFT_RIGHT, Image.FLIP_TOP_BOTTOM, Image.ROTATE_90, Image.ROTATE_180, Image.ROTATE_270]
        img = Util.ConvertArrayToImg(imgArray)
        numpy_array = []

        if (transposeMethod in nonNumberTransposes):
            # Transpose and convert img to array
            img = img.transpose(transposeMethod)  
            numpy_array = numpy.array(img)
        
        # Clockwise rotations (-45,-90,etc.)
        else:
            # Get the img array and change all 0s (black pixels) to an arbitrary value
            temp_array = numpy.array(img)
            temp_array[temp_array <= BLACK_PIXEL_THRESHOLD] = MASK_VALUE
            # print("ImgArray before: ", temp_array)

            # Get the image from temp_array, rotate it, and return the rotated image
            img = Image.fromarray(temp_array,"L").rotate(transposeMethod)

            # Store rotated image's numpy array
            numpy_array = numpy.array(img)

            # Convert all the black pixels generated to white pixels
            numpy_array[numpy_array == 0] = 255

            # Convert all masked values to black pixels
            numpy_array[numpy_array == MASK_VALUE] = 0

        # Convert non 0 values to 1
        for i in range(len(numpy_array)):
            for j in range(len(numpy_array[0])):
                # 255 is white and 0 is black from the original image array
                numpy_array[i][j] = 0 if numpy_array[i][j] >= 255 else 1

        # Util.ArrayToImg(numpy_array)
        return numpy_array