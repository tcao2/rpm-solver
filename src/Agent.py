# Your Agent for solving Raven's Progressive Matrices. You MUST modify this file.
#
# You may also create and submit new files in addition to modifying this file.
#
# Make sure your file retains methods with the signatures:
# def __init__(self)
# def Solve(self,problem)
#
# These methods will be necessary for the project's main method to run.

# Install Pillow and uncomment this line to access image processing.
from PIL import Image, ImageOps, ImageFilter
import numpy
import re
from RPM_Solver import RPM_Solver, RPM_Frame
from Util import *
numpy.set_printoptions(threshold=numpy.nan)

class Agent:
    # The default constructor for your Agent. Make sure to execute any
    # processing necessary before your Agent starts solving problems here.
    #
    # Do not add any variables to this signature; they will not be used by
    # main().
    def __init__(self):
        pass
    
    # The primary method for solving incoming Raven's Progressive Matrices.
    # For each problem, your Agent's Solve() method will be called. At the
    # conclusion of Solve(), your Agent should return an int representing its
    # answer to the question: 1, 2, 3, 4, 5, or 6. Strings of these ints
    # are also the Names of the individual RavensFigures, obtained through
    # RavensFigure.getName(). Return a negative number to skip a problem.
    #
    # Make sure to return your answer *as an integer* at the end of Solve().
    # Returning your answer as a string may cause your program to crash.
    def Solve(self,problem):
        
        # Process 1 problem only
        # print("problem: ", problem.name)
        # currentProblem = "Basic Problem E-12" # Only look at 1 specific problem at a time
        # if (currentProblem == problem.name):
        #     # print("problem: ", problem.name)
        #     currentMatrix = RPM_Solver(problem.name) # Create the problem representation
        #     # print("problem.figures.values()", problem.figures.values())
        #     for image in problem.figures.values(): # Process each image and store as an RPM Frame
        #         # print("image.visualFilename: " +  image.visualFilename)
        #         currentFrame = RPM_Frame(image.visualFilename)
        #         currentFrame.GetFrameName()
        #         currentFrame.GetBWImageArray() # Populate img array of the current frame
        #         currentFrame.LabelComponents()
        #         currentFrame.GetComponents()
        #         currentMatrix.StoreFrames(currentFrame)
        #     currentMatrix.CategorizeFrames()
        #     print(currentMatrix)
        
        #     if (len(currentMatrix.questionFrames) <= 3):
        #         answerStr = currentMatrix.Solve_2x2()
        #     else:
        #         if ("Problem E" in problem.name):
        #             answerStr = currentMatrix.Solve_3x3_E()
        #         else:
        #             answerStr = currentMatrix.Solve_3x3_D()
        #     print("Answer: ", answerStr)

        # return -1

        # Process all problems
        print(problem.name)
        currentMatrix = RPM_Solver(problem.name) # Create the problem representation
        for image in problem.figures.values(): # Process each image and store as an RPM Frame
            currentFrame = RPM_Frame(image.visualFilename)
            currentFrame.GetFrameName()
            currentFrame.GetBWImageArray() # Populate img array of the current frame
            currentFrame.LabelComponents()
            currentFrame.GetComponents()
            currentMatrix.StoreFrames(currentFrame)
        
        currentMatrix.CategorizeFrames() # sort frame into either a choice or a question frame
        if (len(currentMatrix.questionFrames) <= 3):
            return -1
        else:
            if ("Problem D" in problem.name):
                answerStr = currentMatrix.Solve_3x3_D()
            elif ("Problem E" in problem.name):
                answerStr = currentMatrix.Solve_3x3_E()
            else:
                answerStr = currentMatrix.Solve_3x3()

        # Return answer for debugging
        # print("Answer: " , int(answerStr.split('.')[0]))
        # print("\n------------------------------------------------------\n")
        # return int(answerStr.split('.')[0])

        # Return answer for submitting to autograder
        answerStr = answerStr.split('/')[len(answerStr.split('/')) - 1]
        return int(answerStr.split('.')[0])