from PIL import Image, ImageOps, ImageFilter, ImageChops
from Util import Util
import re
import numpy
import copy
import operator

# Global variables that denote common image transformation
FLIP_LR = "FlipLR"
FLIP_TB = "FlipTB"
ROTATE_90 = "Rotate90"
ROTATE_180 = "Rotate180"

# Global for thresold
ARRAY_DIFF_THRESHOLD = 5000 # Threshold for the allowable diff in img array between 2 'identical' shapes with different orientation
BLACK_DIFF_THRESHOLD = 180 # Threshold for the allowable diff in black pixel count between 2 'similar' shapes (identical shapes, or 2 different non-filled shapes)
FILL_DIFF_THRESHOLD = 10000 # If the black diff between 2 figures is greater than this and each figure only has 1 component, 1 figure is filled
#-----------------------------------#
# This class represents the RPM     #
#-----------------------------------#

class RPM_Solver:
    def __init__(self, name):
        self.name = name
        self.questionFrames = []
        self.choiceFrames = []
        self.allFrames = []

    # Method for solving problem sets D
    def Solve_3x3_D(self):
        ROW_SIM_THRESHOLD = 1000 # Determine if all frames in a row is similar
        DIAGONAL_SIM_THRESHOLD = 1100 # Determine if all frames in diagonal are similar

        frameA = self.GetFrameByName("A.png")
        frameB = self.GetFrameByName("B.png")
        frameC = self.GetFrameByName("C.png")
        frameD = self.GetFrameByName("D.png")
        frameE = self.GetFrameByName("E.png")
        frameF = self.GetFrameByName("F.png")
        frameG = self.GetFrameByName("G.png")
        frameH = self.GetFrameByName("H.png")
        answer = ""

        # Check if frames A, B, and C are all the same frame
        diff_AB = self.GetDiffByFrame(frameA, frameB)
        diff_BC = self.GetDiffByFrame(frameB, frameC)
        diff_AC = self.GetDiffByFrame(frameA, frameC)
        avgDiff = (diff_AB + diff_BC + diff_AC)/3.0
        # If the average of diff_AB and diff_BC <= 1000, all frames in each row are the same. The answer should be a frame that is identical
        # to either frame G or frame H
        if avgDiff <= ROW_SIM_THRESHOLD:
            print("avgDiff: ", avgDiff)
            print("All frames in each row are the same")
            answer = self.GetOptimalAnswer(frameH, self.choiceFrames)
            return answer[0]
        else:
            print("Frames in each row are not the same. Proceed to next steps")

        # If all frames in each row isn't the same, we check for the pattern in which the diagonal frames are the same
        diff_AE = self.GetDiffByFrame(frameA, frameE)
        if diff_AE <= DIAGONAL_SIM_THRESHOLD:
            print("diff_AE: ", diff_AE)
            print("Diagonal frames are identical.")
            answer = self.GetOptimalAnswer(frameE,self.choiceFrames)
            return answer[0]

        # Method 1: Get XOR of (A,C) and (G,<eachOfTheChoices>). Then pick the choice that yields the least diff
        answer = RPM_Solver.solveD_xor_then_and(self.allFrames, self.choiceFrames)
        return answer[0]

    # Find the resulting image of XOR-ing (A,C), then get the XOR each of the choices with G. The one that is
    # most similar to XOR'ed (A,C) is the answer
    @staticmethod
    def solveD_xor_then_and(listOfFrames, choiceFrames):
        frameA = RPM_Solver.GetFrameFromList("A.png",listOfFrames)
        frameB = RPM_Solver.GetFrameFromList("B.png",listOfFrames)
        frameC = RPM_Solver.GetFrameFromList("C.png",listOfFrames)

        frameD = RPM_Solver.GetFrameFromList("D.png",listOfFrames)
        frameE = RPM_Solver.GetFrameFromList("E.png",listOfFrames)
        frameF = RPM_Solver.GetFrameFromList("F.png",listOfFrames)

        frameG = RPM_Solver.GetFrameFromList("G.png",listOfFrames)
        frameH = RPM_Solver.GetFrameFromList("H.png",listOfFrames)

        # Get the resulting image from XOR(A,B) | XOR(B,C)
        a_xor_b = RPM_Solver.GetXORImgArray(frameA.imgArray, frameB.imgArray)
        b_xor_c = RPM_Solver.GetXORImgArray(frameB.imgArray, frameC.imgArray)
        row1Combined = RPM_Solver.GetORImgArray(a_xor_b, b_xor_c)

        # Get the resulting image from XOR(D,E) | XOR(E,F)
        d_xor_e = RPM_Solver.GetXORImgArray(frameD.imgArray, frameE.imgArray)
        e_xor_f = RPM_Solver.GetXORImgArray(frameE.imgArray, frameF.imgArray)
        row2combined = RPM_Solver.GetORImgArray(d_xor_e, e_xor_f)

        # Combine row1Combined and row2combined 
        firstRowsCombinedImg = RPM_Solver.GetANDImgArray(row1Combined, row2combined)

        tempDict = {}
        for choice in choiceFrames:
            g_xor_h = RPM_Solver.GetXORImgArray(frameG.imgArray, frameH.imgArray)
            h_xor_choice =  RPM_Solver.GetXORImgArray(frameH.imgArray, choice.imgArray)
            row3Combined = RPM_Solver.GetORImgArray(g_xor_h, h_xor_choice)
            tempDict[choice.frameName] = RPM_Solver.GetDiff(firstRowsCombinedImg, row3Combined)

        answer = str(min(tempDict, key=tempDict.get))
        return [answer, min(tempDict.values())]

    # Method for solving problem sets E
    def Solve_3x3_E(self):
        frameA = self.GetFrameByName("A.png")
        frameB = self.GetFrameByName("B.png")
        frameC = self.GetFrameByName("C.png")
        frameD = self.GetFrameByName("D.png")
        frameE = self.GetFrameByName("E.png")
        frameF = self.GetFrameByName("F.png")
        frameG = self.GetFrameByName("G.png")
        frameH = self.GetFrameByName("H.png")
        answer = ""

        # Phase 1: Check if the dark pixel sum of the last 2 frames in each row is equal to the dark pixel of the last frame
        dpDiff_row1 = abs(frameA.GetBlackPixelCount() -  (frameB.GetBlackPixelCount() + frameC.GetBlackPixelCount()))
        dpDiff_row2 = abs(frameD.GetBlackPixelCount() - (frameE.GetBlackPixelCount() + frameF.GetBlackPixelCount()))
        if (dpDiff_row1 + dpDiff_row2) <= 100:
            expectedDp = frameG.GetBlackPixelCount() - frameH.GetBlackPixelCount()
            candidates = []
            for choice in self.choiceFrames:
                diff = abs(choice.GetBlackPixelCount() - expectedDp)
                # Only add to the candidate list the choice
                if (diff <= 50):
                    candidates.append(choice)
            
            # Find among the candidates the frame that is most similar to frame C
            answer = self.GetOptimalAnswer(frameC,candidates)
            return answer[0]
            
        
        # Phase 2: Get best matched operator between the frames
        prediction = self.GetBestMatchedOperator(self.allFrames)
        answer = self.GetOptimalAnswer(prediction,self.choiceFrames)
        return answer[0]

    # Method for solving 3x3 RPMs
    def Solve_3x3(self):
        frameA = self.GetFrameByName("A.png")
        frameB = self.GetFrameByName("B.png")
        frameC = self.GetFrameByName("C.png")
        frameD = self.GetFrameByName("D.png")
        frameE = self.GetFrameByName("E.png")
        frameF = self.GetFrameByName("F.png")
        frameG = self.GetFrameByName("G.png")
        frameH = self.GetFrameByName("H.png")

        # print(frameA.GetLeftMostPixel())
        # print(frameB.GetLeftMostPixel())
        # print(frameC.GetLeftMostPixel())

        # print(self.GetFrameByName("4.png").GetLeftMostPixel())
        # print(self.GetFrameByName("8.png").GetLeftMostPixel())

        # If A,B,C has the same number of comp., D,E,F have the same number of comp., and G,H have the same number of comp.
        # it means that the answer must have the same number of component as choices G and H
        answer = ""
        if (frameA.components == frameC.components) and (frameD.components ==  frameF.components):
                # If frames A and D has different number of components, it means that each row has the same number 
                # of components, but each column is different. This means frame H MUST have the same number
                # of components as either frame G or H
                if (frameA.components != frameD.components):
                    print("(A,C) has the same number of comp., (D,F) have the same number of comp. (A,C) have different number of comp.")
                    
                    # Filter out the choices that does not have the same num. of comp. as choices G or H
                    candidates = []
                    for choice in self.choiceFrames:
                        if choice.components == frameG.components:
                            candidates.append(choice)
                    
                    self.PrintFrames(candidates)

                    # Pick the answer that yields the least difference to frame H
                    # answer = self.GetOptimalAnswer(frameG,candidates)
                    answer = self.GetMostSimilarFrame(frameG,candidates)

                else:
                    print("All frames SHOULD have the same number of components")

                    # Check the middle frame, frameE. If it has the same number of components with frame A or D,
                    # check for shrink or grow
                    if (frameE.components == frameA.components):
                        print("Middle frame has THE SAME number of components")
                        # Get growth/shrink ratio of AC. We will use this growth/shrink ratio to get frame I from frame G

                        # growShrinkRatio_AC =  self.GetGrowShrinkRatio(frameA,frameC)
                        blackPixelChangeRatio =  self.GetChangeRatio_4Frames(frameA,frameC,frameD,frameF)
                        print("blackPixelChangeRatio: ", blackPixelChangeRatio)
                        candidates = []
                        grow = True # we assume that the image grows from fram A to frame C

                        # If frame A has MORE black pixel than frame C --> the image shrinks instead of grows
                        if (frameA.GetBlackPixelCount() >= frameC.GetBlackPixelCount()) : grow = False

                        # Filter out the choices that does not have the same num. of comp. as choices G
                        for choice in self.choiceFrames:
                            if choice.components == frameG.components:
                                # If the image grows, we only take candidates that have MORE black pixel than frame G
                                if (grow == True):
                                    if (choice.GetBlackPixelCount() > frameG.GetBlackPixelCount()):
                                        candidates.append(choice)
                                # If the image shrinks, we only take candidates that have LESS black pixel than frame G
                                else:
                                    if (choice.GetBlackPixelCount() <= frameG.GetBlackPixelCount()):
                                        candidates.append(choice)

                        # Get the quadrant change list between all frames
                        # print(self.GetQuadrantRatio(frameC, frameA))
                        candidates_2 = [] # Store the 2nd level filtered of the candidates based on quadrant ratios
                        for cand in candidates:
                            # print(self.GetQuadrantRatio(cand,frameG))
                            if (self.GetQuadrantRatio(frameC, frameA) == self.GetQuadrantRatio(cand,frameG)):
                                candidates_2.append(cand)
                        
                        print("Candidates:")
                        self.PrintFrames(candidates_2)

                        # for cand in candidates:
                        #     print("CANDIDATES: " ,cand.frameName)

                        # Return the answer

                        # If we can only find 1 candidate, return it
                        if (len(candidates_2) == 1):
                            answer = [candidates_2[0].frameName, 1]
                        
                        # If there are multiple candidates, return the one with the most similar black pixel change ratio
                        elif (len(candidates_2) > 1):
                            changeRatioDict = {}
                            # Store all the differences between growShrinkRatio(A,C) and growShrinkRatio(eachCandidate,frameG)
                            for cand in candidates_2:
                                changeRatioDict[cand.frameName] = abs(blackPixelChangeRatio - self.GetChangeRatio_2Frames(frameG,cand))

                            # Sort changeRatioDict from smallest to largest (smallest being the ones that are most likely the answer)
                            sorted_changeRatio = sorted(changeRatioDict.items(), key=operator.itemgetter(1))
                            # print("Sorted changeRatio: ", sorted_changeRatio)
                            
                            # If the difference in changeRatio between the 2 frames that are most likely the answer is smaller than 
                            # some arbitrary threshold, we pick the one that is most similar to frame H
                            candidates = []
                            if (abs(sorted_changeRatio[0][1] - sorted_changeRatio[1][1]) <= 0.05):
                                for choice in self.choiceFrames:
                                    if (choice.frameName == sorted_changeRatio[0][0] or choice.frameName == sorted_changeRatio[1][0]):
                                        candidates.append(choice)
                                # print("FINAL CANDIDATE LIST: ")
                                # self.PrintFrames(candidates)
                                # answer = self.GetOptimalAnswer(frameH,candidates)
                                answer = self.GetMostSimilarFrame(frameH,candidates)
                            
                            # If not, we return the smallest
                            else:
                                # Find the candidate with the smallest diff and return answer
                                smallest = min(changeRatioDict.values())
                                for key, value in changeRatioDict.items():
                                    if (value == smallest): 
                                        answer =  [key,value]
                        
                        # If there is no candidate, return 'skipped'
                        else:
                            return "-1.png"

                    # If frameE's component is different from either frame A or D --> there might be some transformations
                    # between frames A,C and frames G,I
                    else:
                        print("Frame E has DIFFERENT of components than frames A,C,D,F")
                        if (frameE.components == frameB.components == frameH.components and frameA.components == 2 and frameC.components == 2 and frameG.components == 2):
                            print("Frames B and E have the same no. of components --> components in frame A move and becomes frame C")
                            components_frameC = frameC.GetSeparateComponents()
                            components_frameA = frameA.GetSeparateComponents()

                            # add 10 because that is our dark pixel ratio threshold
                            moveOffset = abs(RPM_Frame.GetMoveOffset(components_frameC[1],components_frameA[0])) + 10 

                            # Move the first component of frame G by moveOffset, and store its imgArray 
                            components_frameG = frameG.GetSeparateComponents()
                            frameG_comp0_moved = RPM_Frame.MoveLRByOffset(components_frameG[0],moveOffset)
                            # frameG_comp1_moved = RPM_Frame.MoveLRByOffset(components_frameG[1],moveOffset*-1)
                            # combinedG = RPM_Solver.GetCombinedImgArray(frameG_comp0_moved, frameG_comp1_moved)
                            # Util.ArrayToImg(combinedG,"Component_G_combined.png")

                            # Go through the candidates, get the 2nd component (the right most one)
                            # compare its imgArray to frameG_comp0_moved, and get the one with the smallest diff
                            candidateDict = {} # Store the candidates' names, and their 2nd component diffs compared to frameG_comp0_moved
                            for choice in self.choiceFrames:
                                if choice.components == frameG.components:
                                    tempComps = choice.GetSeparateComponents()
                                    tempDiff = RPM_Solver.GetDiff(frameG_comp0_moved,tempComps[1])
                                    candidateDict[choice.frameName] = tempDiff

                            # Return the answer with the smallest diff
                            answer = [str(min(candidateDict, key=candidateDict.get)),0]
                            # answer = "-1.png"
                            # print("Smallest: ", min(candidateDict, key=candidateDict.get))
                            # print("Candidate dict: ", candidateDict ) 

                            # Util.ArrayToImg(frameG_comp0_moved,"Component_G_moved.png")
                            # Util.ArrayToImg(RPM_Frame.MoveLRByOffset(components_frameA[0],moveOffset),"Component_A_0_moved.png")

                        else:
                            print("Frame C is a transformation of frame A")
                            # Filter out the choices that does not have the same num. of comp. as choices G
                            candidates = []
                            for choice in self.choiceFrames:
                                if choice.components == frameG.components:
                                    candidates.append(choice)
                            
                            print("Candidates: ")
                            for cand in candidates:
                                print(cand.frameName)
                            transposedFrame = RPM_Frame.GetClosestMatchedTranspose_v2(frameA,frameC,frameG,candidates)
                            # answer = self.GetOptimalAnswer(transposedFrame[0],candidates)
                            answer = self.GetMostSimilarFrame(transposedFrame[0],candidates)
        
        # If the number of components change between the columns
        else:
            print("Frames (A and C) and (D and F) don't have the same number of components")

            # If the number of component change from A to C and from D to F are the same
            # the change is linear. We only need to add the same number of component to frame G to find frame H
            if (frameC.components - frameA.components == frameF.components - frameD.components):
                print("Number of component change MIGHT BE linear")
                componentDiff = frameF.components - frameD.components
                print("Component diff: ", componentDiff)
                print("Answer should have: ", frameG.components + componentDiff, " components")

                # Filter out the choices that does not have the expected number of components
                candidates = []
                for choice in self.choiceFrames:
                    if choice.components == frameG.components + componentDiff:
                        candidates.append(choice)
                
                # If there is only 1 candidate, return it
                if (len(candidates) >= 1):
                    # answer = self.GetOptimalAnswer(frameH,candidates)
                    answer = self.GetMostSimilarFrame(frameH,candidates)
                # If we cannot find any candidate, attempt to find the change ratio between frames E and F
                else:
                    candidates = []
                    print("Number of component change IS NOT linear!!")
                    ratio = frameF.components/frameE.components
                    for choice in self.choiceFrames:
                        if choice.components == frameH.components*ratio:
                            candidates.append(choice)
                    
                    # If we cannot find any candidate, return 'skipped'
                    if (len(candidates) == 0): 
                        return "-1.png"
                    # answer = self.GetOptimalAnswer(frameH,candidates)
                    answer = self.GetMostSimilarFrame(frameH,candidates)

            
            # If it is NOT linear, we need to find the ratio of component change
            else:
                ratio = 1
                ratio = float(frameF.components)/float(frameD.components)
                print("Ratio: ", ratio)

                # Filter out the choices that does not have the expected number of components
                candidates = []
                for choice in self.choiceFrames:
                    if choice.components == frameG.components*ratio:
                        candidates.append(choice)

                print("CANDIDATES: ")
                for cand in candidates:
                    print(cand.frameName)
                
                # If there are some candidates, go through them and pick 1 as the answer
                if (len(candidates) >= 1):
                    # answer = self.GetOptimalAnswer(frameC,candidates)

                    answer = self.GetMostSimilarFrame(frameC,candidates)
                
                # If no candidate is found --> the components might have different fill levels. Attempt another method
                else:
                    print("Component have different fill levels")
                    # If the last 2 pairs of frames in the 3rd row and column have the same number of components
                    # it means the last frame will also have that same number of component, might be just different
                    # fill level
                    if (frameC.components == frameF.components and frameG.components == frameH.components):
                        candidates = []
                        print("The answer should have ", frameC.components, " components")

                        # Go through the choices and only store the ones with the same number of components as frame F to
                        # the candidate list
                        if (frameF.GetBlackPixelCount() > frameC.GetBlackPixelCount()):
                            print("Answer should have MORE black pixel than frame F")
                            for choice in self.choiceFrames:
                                if (choice.components == frameF.components and choice.GetBlackPixelCount() > frameC.GetBlackPixelCount()):
                                    candidates.append(choice)
                        else:
                            print("Answer should have LESS black pixel than frame F")
                            for choice in self.choiceFrames:
                                if (choice.components == frameF.components and choice.GetBlackPixelCount() <= frameC.GetBlackPixelCount()):
                                    candidates.append(choice)

                        self.PrintFrames(candidates)

                        # If we can only find 1 candidate, return it
                        if (len(candidates) == 1):
                            answer = [candidates[0].frameName, 1]
                        
                        # If there are multiple candidates, return the one with the most similar black pixel change ratio
                        elif (len(candidates) > 1):
                            blackPixelChangeRatio = self.GetChangeRatio_4Frames(frameC,frameF,frameG,frameH)
                            print("changeRatio: ", blackPixelChangeRatio)
                            changeRatioDict = {}
                            # Store all the differences between growShrinkRatio(A,C) and growShrinkRatio(eachCandidate,frameG)
                            for cand in candidates:
                                print("Change ratio between frameF and ", cand.frameName, ": ", self.GetChangeRatio_2Frames(frameF,cand))
                                temp = abs(blackPixelChangeRatio - self.GetChangeRatio_2Frames(frameF,cand))
                                if (temp >= 0.1):
                                    changeRatioDict[cand.frameName] = abs(blackPixelChangeRatio - self.GetChangeRatio_2Frames(frameF,cand))
                            print("changeRatioDict: ", changeRatioDict)
                            # Find the candidate with the smallest diff and return answer
                            smallest = min(changeRatioDict.values())
                            for key, value in changeRatioDict.items():
                                if (value == smallest): 
                                    answer =  [key,value]

                        # self.PrintFrames(candidates)
                        # # If there are some candidates, go through them and pick 1 as the answer
                        # if (len(candidates) >= 1):
                        #     answer = self.GetOptimalAnswer(frameH,candidates)

        # Return answer 
        if (answer):
            return answer[0]
        return "-1.png"

    # Prints a list of frames
    @staticmethod
    def PrintFrames(frameList):
        print("\nList of frames: ")
        for frame in frameList:
            print(frame.frameName)
        print("\n")

    # Method to find the growth ratio between 2 frames (get distance between the left most pixel of 2 frames)
    @staticmethod
    def GetGrowShrinkRatio(frameA, frameB):
        frameAFirstPixelCoord = frameA.GetLeftMostPixel()
        frameBFirstPixelCoord = frameB.GetLeftMostPixel()

        distance = (float(frameAFirstPixelCoord[0] - frameBFirstPixelCoord[0])**2 + (frameAFirstPixelCoord[1] - frameBFirstPixelCoord[1])**2)
        distance = distance**(1.0/2)

        print("Distance between frames: ", frameA.frameName, frameB.frameName, ": ", distance )
        return distance

    # Finds the change ratio between 2 pairs of 2 frames, and return the average
    @staticmethod
    def GetChangeRatio_4Frames(frame1, frame2, frame3, frame4):
        ratio = (float(frame2.GetBlackPixelCount())/float(frame1.GetBlackPixelCount()) + float(frame4.GetBlackPixelCount())/float(frame3.GetBlackPixelCount()))/2
        # print("Change ratio: ", ratio)
        return ratio
    
    @staticmethod
    def GetChangeRatio_2Frames(frame1, frame2):
        ratio = float(frame2.GetBlackPixelCount())/float(frame1.GetBlackPixelCount())
        # print("Change ratio between ", frame1.frameName, " and frame ", frame2.frameName, " : ", ratio)
        # print(ratio)
        return ratio

    # Return the number representing how dpr of the 4 quadrants change from frame1 to frame2
    # 0 means the DP is the same; -1 means the DP decreases, and 1 means the DP increases
    @staticmethod
    def GetQuadrantRatio(frame1, frame2):
        # print("\n")
        # print("Quadrant diffs between: ", frame1.frameName, " and ", frame2.frameName)
        frame1Quadrant = frame1.GetQuadrants()
        frame2Quadrant = frame2.GetQuadrants()
        blackPixelDiff = []
        for index, item in enumerate(frame1Quadrant, start=0): 
            blackPixelDiff.append(Util.GetBlackPixelCount(item) - Util.GetBlackPixelCount(frame2Quadrant[index]))

        # print("BlackPixelDiff BEFORE conversion: ", blackPixelDiff)

        # Change the values in blackPixelDiff to either -1,0,or 1 depending on the threshold of 100
        for index, item in enumerate(blackPixelDiff,start=0):
            if (item > 100):
                blackPixelDiff[index] = 1
            elif (item >= -100 and item <= 100):
                blackPixelDiff[index] = 0
            else:
                blackPixelDiff[index] = -1
        # print("BlackPixelDiff AFTER conversion: ", blackPixelDiff)
        # print("Sum: ", sum(blackPixelDiff))
        return sum(blackPixelDiff)
        

    # Method for solving 2x2 RPMs
    def Solve_2x2(self):
        answer = ""
        # Get all frames in question frames
        frameA = self.GetFrameByName("A.png")
        frameB = self.GetFrameByName("B.png")
        frameC = self.GetFrameByName("C.png")

        # Get component relationships between frames
        compDiff_AB = frameA.components - frameB.components
        compDiff_AC = frameA.components - frameC.components

        # Get black pixels relationships between the frames. 
        blackDiff_AB = abs(frameA.GetBlackPixelCount() - frameB.GetBlackPixelCount())
        blackDiff_AC = abs(frameA.GetBlackPixelCount() - frameC.GetBlackPixelCount())
        blackDiff_BC = frameB.GetBlackPixelCount() - frameC.GetBlackPixelCount()
        print("blackDiff_AB: ", blackDiff_AB, " | blackDiff_AC: ", blackDiff_AC, " | blackDiff_BC: ", blackDiff_BC)
        
        # Get img array relationships between the frames
        arrayDiff_AB = self.GetDiffByImgName("A.png","B.png")
        arrayDiff_AC = self.GetDiffByImgName("A.png","C.png")
        print("arrayDiff_AB: ", arrayDiff_AB, " | arrayDiff_AC: ", arrayDiff_AC)

        # If there is no diff in the number of components between A & B and A & C
        if compDiff_AB == 0 and compDiff_AC == 0:
            # THRESHOLD = 180 # Threshold for the allowable diff in black pixel count between 2 'identical' shapes
            
            # If black pixel count diff between them is within the threshold
            # it means that the frames SHOULD have identical size and shape, but they
            # might have different orientation
            if (blackDiff_AB <= BLACK_DIFF_THRESHOLD and blackDiff_AC <= BLACK_DIFF_THRESHOLD):
                
                # Diff in img array is within a threshold -> all frames should be identical (size,shape,orientation) 
                # -> choose a frame similar to any question frame
                if (arrayDiff_AB <= 10 and arrayDiff_AC <= 10):
                    answer = self.GetOptimalAnswer(frameA,self.choiceFrames)

                # If there is diff in img array, it means that they are of identical
                # size, shape, and fillings, but different orientation. We will check if the difference
                # in orientation is between (A&B) or (A&C), and find that relationship
                else:
                    # If there is NO image transpose from A -> B and there IS image transpose from A -> C
                    # it means that A&B are identical, while A&C are of the same shape and size, but 
                    # different orientation
                    if (arrayDiff_AB <= ARRAY_DIFF_THRESHOLD and arrayDiff_AC > ARRAY_DIFF_THRESHOLD):
                        print("arrayDiff_AB <= threshold and arrayDiff_AC > threshold")
                        transposedFrame = RPM_Frame.GetClosestMatchedTranspose_v2(frameA,frameC,frameB,self.choiceFrames)
                        answer = self.GetOptimalAnswer(transposedFrame[0],self.choiceFrames)

                    #  If there is NO image transpose from A -> C and there IS image transpose from A -> B
                    elif (arrayDiff_AB > ARRAY_DIFF_THRESHOLD and arrayDiff_AC <= ARRAY_DIFF_THRESHOLD):
                        print("(arrayDiff_AB > threshold and arrayDiff_AC <= threshold")
                        transposedFrame = RPM_Frame.GetClosestMatchedTranspose_v2(frameA,frameB,frameC,self.choiceFrames)
                        answer = self.GetOptimalAnswer(transposedFrame[0],self.choiceFrames)

                    # If there IS img transpose from BOTH A->C AND A->B:
                    elif (arrayDiff_AB <= ARRAY_DIFF_THRESHOLD and arrayDiff_AC <= ARRAY_DIFF_THRESHOLD):
                        print("arrayDiff_AB <= threshold and arrayDiff_AC <= threshold")
                        # Since all the images are the same but just different
                        # in orientation, we don't care about the transpose from A->B and
                        # only check for the transpose from A->C, then
                        # apply that transpose on B to get the answer
                        transposedFrame = RPM_Frame.GetClosestMatchedTranspose_v2(frameA,frameB,frameC,self.choiceFrames) # Testing
                        answer = self.GetOptimalAnswer(transposedFrame[0],self.choiceFrames)
                    else:
                        print("arrayDiff_AB > threshold and arrayDiff_AC > threshold")
                        # Since all the images are the same but just different
                        # in orientation, we don't care about the transpose from A->B and
                        # only check for the transpose from A->C, then
                        # apply that transpose on B to get the answer
                        transposedFrame = RPM_Frame.GetClosestMatchedTranspose_v2(frameA,frameB,frameC,self.choiceFrames) # Testing
                        answer = self.GetOptimalAnswer(transposedFrame[0],self.choiceFrames)

            # If AB > threshold and AC <= threshold --> A and C are of the same shape
            # 
            elif (blackDiff_AB > BLACK_DIFF_THRESHOLD and blackDiff_AC <= BLACK_DIFF_THRESHOLD):
                print("blackDiff_AB > BLACK_DIFF_THRESHOLD and blackDiff_AC <= BLACK_DIFF_THRESHOLD")
                # If blackDiff between A and C is within the threshold, there might be 2 cases:
                # 1. A and C are of identical shapes. If this is the case, we just find D such that B == D
                # 2. A and C are non-filled (different) shapes. If this is the case, we combine frame
                # C with each of the filled frame in the choices (call this frame combined), and compare
                # frame 'combined' with each of the choice. The one that yields the smallest diff is the answer!
                
                # OLD CODE AND WORKING START
                # Check if scenario 2 is the case here
                if (frameA.GetFillLevel() < 10 and frameC.GetFillLevel() < 10 and frameB.GetFillLevel() > 30):
                    frameA_Fill = frameA.GetFillLevel()
                    frameB_Fill = frameB.GetFillLevel()
                    frameC_Fill = frameC.GetFillLevel()
                    candidates = [] # Store the candidates
                    # potentialAnswers = {} # Store potential answers and the diffs
                    targetFrame = frameA # Store the target frame, which we will use to compare and get the answer
                    if (abs(frameA_Fill - frameC_Fill) <= abs(frameA_Fill - frameB_Fill)):
                        targetFrame = frameC
                        print("Frame A and C have the same fill level")
                        # Filter the candidates and store into another list
                        for frame in self.choiceFrames:
                            # print(frame.frameName, " fill level diff with frame B :", abs(frame.GetFillLevel() - frameB_Fill))
                            if (abs(frame.GetFillLevel() - frameB_Fill) <= 10):
                                candidates.append(frame)

                    else:
                        print("Frame A and B have the same fill level")
                        targetFrame = frameB
                        # Filter the candidates and store into another list
                        for frame in self.choiceFrames:
                            print("Fill diff frame ", frame.frameName, " and frame C: ", abs(frame.GetFillLevel() - frameC_Fill))
                            if (abs(frame.GetFillLevel() - frameC_Fill) <= 10):
                                candidates.append(frame)
                        
                    # If there is only 1 candidate in the list, return that candidate
                    if (len(candidates) == 1):
                        print("Only 1 candidate")
                        return candidates[0].frameName
                    # If there is 0 candidate, return -1 (skipped)
                    elif (len(candidates) == 0):
                        return "-1.png"
                    # If there are more than 1 candidates, get the 1 that is closest to B
                    else:
                        # Print the candidates
                        # print("Candidates:")
                        # for cand in candidates:
                        #     print(cand.frameName)
                        # print("Target frame is: ", targetFrame.frameName)

                        # print("Target frame is: ", targetFrame.frameName)

                        # Fill the target frame's image array, and return the img array
                        filledImgArray = RPM_Frame.GetFilledImgArray(targetFrame)

                        # Util.ArrayToImg(filledImgArray,"targetFrame.png")

                        answer = self.GetOptimalAnswerFromImgArray(filledImgArray,candidates)
                
                # If frame A and C are filled and frame B is non-filled ==> D MUST BE NON-FILLED!
                # And since blackDiff_AC <= black_diff_threshold, D must be VERY SIMILAR TO B   
                elif (frameA.GetFillLevel() > 30 and frameC.GetFillLevel() > 30 and frameB.GetFillLevel() < 10):
                    print("Frame A and B have the same fill level (filled)")
                    answer = self.GetOptimalAnswer(frameB,self.choiceFrames)

                # If scenario 1 is the case
                else:
                    # transposedFrame = RPM_Frame.GetClosestMatchedTranspose(frameA,frameC,frameB,self.choiceFrames) -- Original and working!
                    transposedFrame = RPM_Frame.GetClosestMatchedTranspose_v2(frameA,frameC,frameB,self.choiceFrames) # -- Testing
                    answer = self.GetOptimalAnswer(transposedFrame[0],self.choiceFrames)
            
            # If AC > Threshold and AB <= threshold --> A and B might be of the same shape OR A and B have the same fill level
            # which means D has the same fill level as C
            elif (blackDiff_AC > BLACK_DIFF_THRESHOLD and blackDiff_AB <= BLACK_DIFF_THRESHOLD):
                print("blackDiff_AC > BLACK_DIFF_THRESHOLD and blackDiff_AB <= BLACK_DIFF_THRESHOLD")
                # If frame A and B are non-filled, and frame C is filled ==> D MUSE BE FILLED!
                if (frameA.GetFillLevel() < 10 and frameB.GetFillLevel() < 10 and frameC.GetFillLevel() > 30):
                    frameA_Fill = frameA.GetFillLevel()
                    frameB_Fill = frameB.GetFillLevel()
                    frameC_Fill = frameC.GetFillLevel()
                    candidates = [] # Store the candidates
                    # potentialAnswers = {} # Store potential answers and the diffs
                    targetFrame = frameA # Store the target frame, which we will use to compare and get the answer

                    if (abs(frameA_Fill - frameC_Fill) <= abs(frameA_Fill - frameB_Fill)):
                        print("Frame A and C have the same fill level (non-filled)")
                        targetFrame = frameC
                        # Filter the candidates and store into another list
                        for frame in self.choiceFrames:
                            # print(frame.frameName, " fill level diff with frame B :", abs(frame.GetFillLevel() - frameB_Fill))
                            if (abs(frame.GetFillLevel() - frameB_Fill) <= 10):
                                candidates.append(frame)

                    else:
                        print("Frame A and B have the same fill level")
                        targetFrame = frameB
                        # Filter the candidates and store into another list
                        for frame in self.choiceFrames:
                            if (abs(frame.GetFillLevel() - frameC_Fill) <= 10):
                                candidates.append(frame)
                        
                    # If there is only 1 candidate in the list, return that candidate
                    if (len(candidates) == 1):
                        print("Only 1 candidate")
                        return candidates[0].frameName
                    # If there is 0 candidate, return -1 (skipped)
                    elif (len(candidates) == 0):
                        return "-1.png"
                    # If there are more than 1 candidates, get the 1 that is closest to B
                    else:
                        # Print the candidates
                        print("Target frame is: ", targetFrame.frameName)

                        # Fill the target frame's image array, and return the img array
                        filledImgArray = RPM_Frame.GetFilledImgArray(targetFrame)

                        # Util.ArrayToImg(filledImgArray,"targetFrame.png")

                        answer = self.GetOptimalAnswerFromImgArray(filledImgArray,candidates)

                # If frame A and B are filled and frame C is non-filled ==> D MUST BE NON-FILLED!
                # And since blackDiff_AB <= black_diff_threshold, D must be VERY SIMILAR TO C   

                elif(frameA.GetFillLevel() > 30 and frameB.GetFillLevel() > 30 and frameC.GetFillLevel() < 10):
                    print("Frame A and B have the same fill level (filled)")
                    answer = self.GetOptimalAnswer(frameC,self.choiceFrames)

                # NEED TO COME BACK TO THIS!!!
                else:
                    # Store all frame with the same fill level as frame C into the candidates list
                    candidates = []
                    for frame in self.choiceFrames:
                        if (abs(frame.GetFillLevel() - frameC.GetFillLevel()) <= 4):
                            candidates.append(frame)

                    # Print candidates
                    for frame in candidates:
                        print("candidate: ", frame.frameName)

                    # Have this condition to prevent exception
                    if (len(candidates) == 0):
                        return "-1.png"
            
                    transposedFrame = RPM_Frame.GetClosestMatchedTranspose_v2(frameA,frameB,frameC,candidates)
                    answer = self.GetOptimalAnswer(transposedFrame[0],candidates)

                # return "-1.png" # REMOVE WHEN DONE!
            
            # TO BE IMPLEMENTED
            # This is when 2 frames are filled and 1 frame is non-filled, and the 2 filled frames have different shapes
            else:
                print("blackDiff_AC > BLACK_DIFF_THRESHOLD and blackDiff_AB > BLACK_DIFF_THRESHOLD")
                frameA_Fill = frameA.GetFillLevel()
                frameB_Fill = frameB.GetFillLevel()
                frameC_Fill = frameC.GetFillLevel()

                # print("FrameA_Fill: ", frameA_Fill)
                # print("FrameB_Fill: ", frameB_Fill)
                # print("FrameC_Fill: ", frameC_Fill)
                # Testing
                # print("Diff BC: ", self.GetDiffByImgName("B.png","C.png"))
                # print("Diff 4C: ", self.GetDiffByImgName("4.png","C.png"))

                candidates = []
                targetFrame = frameA
                # If A and C have the same fill level which is different from B, then D will have the same fill level as B
                if (abs(frameA_Fill - frameC_Fill) <= abs(frameA_Fill - frameB_Fill)):
                    targetFrame = frameC
                    print("Frame A and C have the same fill level")
                    # Filter the candidates and store into another list
                    for frame in self.choiceFrames:
                        # print(frame.frameName, " fill level diff with frame B :", abs(frame.GetFillLevel() - frameB_Fill))
                        if (abs(frame.GetFillLevel() - frameB_Fill) <= 5.0):
                            candidates.append(frame)

                    # print("Candidates: ")
                    # for cand in candidates:
                    #     print(cand.frameName)

                    # # If there is only 1 candidate in the list, return that candidate
                    # if (len(candidates) == 1):
                    #     print("Only 1 candidate")
                    #     return candidates[0].frameName
                    # # If there is 0 candidate, return -1 (skipped)
                    # elif (len(candidates) == 0):
                    #     return "-1.png"
                    # # If there are more than 1 candidates, we fill all the candidates and choose the 1 that is closest to C
                    # else:
                    #     answer = self.GetOptimalAnswer(frameC,candidates)
                    

                # If A and B have the same fill level which is different from C, then D will have the same fill level as C
                else:
                    print("Frame A and B have the same fill level")
                    targetFrame = frameB
                    # Filter the candidates and store into another list
                    for frame in self.choiceFrames:
                        if (abs(frame.GetFillLevel() - frameC_Fill) <= 5):
                            candidates.append(frame)

                # If there is only 1 candidate in the list, return that candidate
                if (len(candidates) == 1):
                    # print("Only 1 candidate")
                    return candidates[0].frameName
                # If there is 0 candidate, return -1 (skipped)
                elif (len(candidates) == 0):
                    return "-1.png"
                # If there are more than 1 candidates, we fill all the candidates, and choose the 1 that is closest to the target frame
                else:
                    # print("target frame: ", targetFrame.frameName)
                    # print("Candidates: ")
                    # for cand in candidates:
                    #     print(cand.frameName)

                    potentialAns = {}
                    for frame in candidates:
                        filledImgArray = RPM_Frame.GetFilledImgArray(frame)
                        potentialAns[frame.frameName] = RPM_Solver.GetDiff(targetFrame.imgArray,filledImgArray)

                    # print("PotentialAns: ", potentialAns)
                    for key,value in potentialAns.items():
                        if (value == min(potentialAns.values())):
                            answer = [key,value]
                            break

                    # answer =  self.GetOptimalAnswer(targetFrame,candidates)

                # return "-1.png"

        # If there is component differences between the images
        else: 
            # If extra comp. added to/removed from to C 
            if (compDiff_AB == 0 and compDiff_AC != 0):
                # Get the extra component and store into a separate img array
                compImgArray = RPM_Solver.GetImgArrayDiff(frameA.imgArray,frameC.imgArray)
                
                # If frameC has MORE components than frameA
                if (compDiff_AC < 0): 
                    print("compDiff_AB == 0 and compDiff_AC != 0. C has MORE components than A")

                    # First check if frame B is a transpose of frame A or not
                    transposedFrame = RPM_Frame.GetClosestMatchedTranspose_v2(frameA,frameB,frameC,self.choiceFrames)
                    tempAnswer = self.GetOptimalAnswer(transposedFrame[0],self.choiceFrames)
                    if (transposedFrame[1] == True and tempAnswer[1] <= 1500):
                        answer = tempAnswer
                    else:
                        # If there is no relationship between frame A and frame B found,
                        # get the predicted img array  by adding the extra component(s) found to frameB
                        predictedImgArray = RPM_Solver.GetCombinedImgArray(compImgArray,frameB.imgArray)
                        answer = self.GetOptimalAnswerFromImgArray(predictedImgArray,self.choiceFrames)

                # If frameC has LESS components than frameA
                else:
                    print("compDiff_AB == 0 and compDiff_AC != 0. C has LESS components than A")

                    # First check if frame B is a transpose of frame A or not
                    transposedFrame = RPM_Frame.GetClosestMatchedTranspose_v2(frameA,frameB,frameC,self.choiceFrames)
                    tempAnswer = self.GetOptimalAnswer(transposedFrame[0],self.choiceFrames)
                    if (transposedFrame[1] == True and tempAnswer[1] <= 1500):
                        answer = tempAnswer
                    else:
                        # If there is no relationship between frame A and frame B found,
                        # Get the predicted img array by subtracting the adition component(s) from frame B
                        predictedImgArray = RPM_Solver.GetImgArrayDiff(compImgArray,frameB.imgArray)
                        answer = self.GetOptimalAnswerFromImgArray(predictedImgArray,self.choiceFrames)
                    

                # Print optimal answer
                # answer = self.GetOptimalAnswerFromImgArray(predictedImgArray,self.choiceFrames)
                print("Answer: ", answer)


            # If extra comp. added to/removed from B
            elif (compDiff_AB != 0 and compDiff_AC == 0):
                print("compDiff_AB != 0 and compDiff_AC == 0")
                # Get the extra component and store into a separate img array
                compImgArray = RPM_Solver.GetImgArrayDiff(frameA.imgArray,frameB.imgArray)

                # if frameB has MORE components than frameA
                if (compDiff_AB < 0): 
                    print("compDiff_AB != 0 and compDiff_AC == 0. B has MORE components than A")

                    # First check if frame C is a transpose of frame A or not
                    transposedFrame = RPM_Frame.GetClosestMatchedTranspose_v2(frameA,frameC,frameB,self.choiceFrames)
                    tempAnswer = self.GetOptimalAnswer(transposedFrame[0],self.choiceFrames)
                    if (transposedFrame[1] == True and tempAnswer[1] <= 1500):
                        answer = tempAnswer
                    else:
                        # If there is no relationship between frame A and frame C found,
                        # Get the predicted img array by adding the extra component found to frameC
                        predictedImgArray = RPM_Solver.GetCombinedImgArray(compImgArray,frameC.imgArray)
                        answer = self.GetOptimalAnswerFromImgArray(predictedImgArray,self.choiceFrames)

                # if frame B has LESS components than frameA
                else: 
                    print("compDiff_AB != 0 and compDiff_AC == 0. B has LESS components than A")

                    # First check if frame C is a transpose of frame A or not
                    transposedFrame = RPM_Frame.GetClosestMatchedTranspose_v2(frameA,frameC,frameB,self.choiceFrames)
                    tempAnswer = self.GetOptimalAnswer(transposedFrame[0],self.choiceFrames)
                    if (transposedFrame[1] == True and tempAnswer[1] <= 1500):
                        answer = tempAnswer
                    else:
                        # If there is no relationship between frame A and frame C found,
                        # Get the predicted img array by subtracting the adition component from frame C
                        predictedImgArray = RPM_Solver.GetImgArrayDiff(compImgArray,frameC.imgArray)
                        answer = self.GetOptimalAnswerFromImgArray(predictedImgArray,self.choiceFrames)

                # Get optimal answer
                # answer = self.GetOptimalAnswerFromImgArray(predictedImgArray,self.choiceFrames)
                print("Answer: ", answer)

            # If extra comp. added to/removed from both B and C
            # For 2x2 matrices, comp.Diff(A,C) == comp.Diff(A,B). We just need to find either diff
            else:
                print("compDiff_AB != 0 and compDiff_AC != 0")
                answerNumOfComp = self.GetFrameByName("B.png").components
                # Figure out the predicted number of component in the answer
                if (compDiff_AB > 0): 
                    answerNumOfComp -= compDiff_AB
                else:
                    answerNumOfComp -= -compDiff_AB

                # Get the frame we will use to get the answer
                relatedFrame = self.GetFrameByName("B.png")
                if (blackDiff_BC < 0):
                    relatedFrame = self.GetFrameByName("C.png")

                # Store all candidates (frame with 'components' == answerNumOfComp) to a list, along with
                # their black pixel counts
                candidates = {}
                for frame in self.choiceFrames:
                    if frame.components == answerNumOfComp: 
                        candidates[frame.frameName] = frame.GetBlackPixelCount()

                # if the number of black pixel counts increases, there must have been some fillings. 
                # We will choose the answer base on the followings:
                    # 1. Same number of component as answerNumOfComp
                    # 2. Has MORE black pixel than frame B/C
                    # 3. Has the smallest number of black pixel among all candidates
                if (relatedFrame.GetBlackPixelCount() >= frameA.GetBlackPixelCount()):
                    # Remove the candidates whose black pixel count is < relatedFrame
                    for frameName,blackPix in candidates.items():
                        if (blackPix < relatedFrame.GetBlackPixelCount()):
                            del candidates[frameName]

                    # Do this to avoid execution error when there is 0 candidates
                    if (len(candidates) == 0):
                        answer = ["-1.png",99]
                    else:
                        # Get the one with the smallest black pixel count
                        smallest = min(candidates.values())
                        for key,value in candidates.items():
                            if (value == smallest):
                                answer = [key,value]
                                break

                # Else, we choose the answer base on the followings: 
                    # 1. Same number of component as answerNumOfComp
                    # 3. Has the smallest number of black pixel among all candidates
                else:
                    # Do this to avoid execution error when there is 0 candidates
                    print("candidates[]: ", candidates)
                    if (len(candidates) == 0):
                        answer = ["-1.png",99]
                    else:
                        # Get the one with the smallest black pixel count
                        smallest = min(candidates.values())
                        for key,value in candidates.items():
                            if (value == smallest):
                                answer = [key,value]
                                break

                # answer = ["-1",99]
        return answer[0]

    # Search in choices<frame> a frame that is most similar to a given frame
    def GetOptimalAnswer(self,frame,choices):
        tempDict = {}
        # Store all the diffs between a given frame and all the choices into a dict.
        for choice in choices:
            # tempDiff = self.GetDiffByImgName(frame.frameName,choice.frameName) # OLD AND WORKING
            tempDiff = self.GetDiffByFrame(frame,choice)
            
            print("frame: " + choice.frameName + " - diff: ", tempDiff)
            tempDict[choice.frameName] = abs(tempDiff)

        # Find the smallest value and return a number
        # bestMatch = str(min(tempDict, key=tempDict.get))
        # return [bestMatch,min(tempDict.values())]

        smallest = min(tempDict.values())
        for key, value in tempDict.items():
            if (value == smallest): 
                print("Smallest diff found: ", value)
                return [key,value]

    # Search in choices<frame> for the frame that is most similar to a given frame by doing the following:
    # - XOR-ing the img array of the frame and each of the choice
    # - Subtract the original black pixel count of the choice from the XOR-ed img array black pixel count, store them in a dictionary
    # - The one that is the smallest will be the answer. Explanation: When XOR-ing 2 img arrays, the more similar the frames,
    # - the more black pixels will be removed, which results in the XOR-ed img array having less black pixel than the original choice's img array
    def GetMostSimilarFrame(self,frame,choices):
        tempDict = {}
        for choice in choices:
            diffXOR = RPM_Solver.GetDiff_XOR(frame.imgArray,choice.imgArray)
            tempDict[choice.frameName] = diffXOR - choice.GetBlackPixelCount()
        
        # print("Temp dict in GetMostSimilarFrame(): ", tempDict)
        
        # Find and return the smallest value
        answer = [str(min(tempDict, key=tempDict.get)),min(tempDict.values())]
        return answer

    # Search in choices<frame> a frame that is most similar to a given imgArray
    def GetOptimalAnswerFromImgArray(self,imgArray,choices):
        tempDict = {}
        # Store all the diffs between a given frame and all the choices into a dict.
        for choice in choices:
            tempDiff = self.GetDiff(imgArray,choice.imgArray)
            tempDict[choice.frameName] = abs(tempDiff)

        print(tempDict)
        # Find the smallest value and return a number
        smallest = min(tempDict.values())
        for key, value in tempDict.items():
            if (value == smallest): 
                print("Smallest diff found: key: ", key, " value: ", value)
                return [key,value]

    # Return a str representation of a problem
    def __str__(self):
        returnStr = "Matrix's name: " + self.name + "\nQuestion frames: \n"
        for frame in self.questionFrames:
            returnStr+= frame.frameName + " | Component(s): " + str(frame.components) + " | Black Pixel: " + str(frame.GetBlackPixelCount()) + "\n"
       
        returnStr+= "\nChoice frames: \n"

        for choice in self.choiceFrames:
            returnStr+= choice.frameName + " | Component(s): " + str(choice.components) + " | Black Pixel: " + str(choice.GetBlackPixelCount()) + "\n"
        return returnStr

    

    # Traverse through all frames in a problem, and label them as either
    # a question frame, or a choice frame
    def CategorizeFrames(self):
        for frame in self.allFrames:
            if ("A.png" in frame.fileName or "B.png" in frame.fileName or "C.png" in frame.fileName or "D.png" in frame.fileName or "E.png" in frame.fileName or "F.png" in frame.fileName or "G.png" in frame.fileName or "H.png" in frame.fileName):
                self.questionFrames.append(frame)
            else:
                self.choiceFrames.append(frame)

    # Store currentFrame into the list of all frames from a problem
    def StoreFrames(self,currentFrame):
        self.allFrames.append(currentFrame)

    # Search for a frame with name 'frameName'. Return type: an RPM_Frame object
    def GetFrameByName(self,frameName):
        for frame in self.allFrames:
            if (frameName in frame.fileName):
                return frame

    @staticmethod
    def GetFrameFromList(frameName, listOfFrames):
        for frame in listOfFrames:
            if (frameName in frame.fileName):
                return frame

    # Return bitwise XOR of array1 and array2. Return type: a numpy array
    @staticmethod
    def GetImgArrayDiff(array1, array2):
        return numpy.bitwise_xor(array1,array2)
    
    # Return bitwise OR of array1 and array2. Return type: a numpy array
    @staticmethod
    def GetCombinedImgArray(array1, array2):
        return numpy.bitwise_or(array1,array2)

    # Return bitwise AND of array1 and array2. Return type: a numpy array
    @staticmethod
    def GetBitWiseAndImgArray(array1, array2):
        return numpy.bitwise_and(array1, array2)
    
    # Subtract imgArrayB from imgArrayA, take the absolute value, and return the number
    # of cell that are NOT 0. Return type: int
    @staticmethod
    def GetDiff(imgArrayA, imgArrayB):
        diffMatrix =  abs(numpy.array(imgArrayA) - numpy.array(imgArrayB))
        # diffPixelCount = 0

        return numpy.count_nonzero(diffMatrix)

        # Get the diff pixel count using nditer
        # for pixel in numpy.nditer(diffMatrix):
        #     if pixel != 0: diffPixelCount+=1
        # return diffPixelCount
    
    # Testing code for getting diff. Return type: int
    @staticmethod
    def GetDiff_Test(imgArrayA, imgArrayB):
        diffMatrix =  abs(numpy.array(imgArrayA) - numpy.array(imgArrayB))
        # diffPixelCount = 0
        Util.ArrayToImg(diffMatrix, "GetDiff.png")

        return numpy.count_nonzero(diffMatrix)

        # Get the diff pixel count using nditer
        # for pixel in numpy.nditer(diffMatrix):
        #     if pixel != 0: diffPixelCount+=1
        # print("GetDiff_Test Black count: ", diffPixelCount)
        # return diffPixelCount

    # Get logical XOR of 2 image arrays
    @staticmethod
    def GetXORImgArray(arrayA, arrayB):
        return numpy.bitwise_xor(arrayA,arrayB)
    
    # Get logical AND of 2 image arrays
    @staticmethod
    def GetANDImgArray(arrayA, arrayB):
        return numpy.bitwise_and(arrayA, arrayB)

    # Get logical OR of 2 image arrays
    @staticmethod
    def GetORImgArray(arrayA, arrayB):
        return numpy.bitwise_or(arrayA, arrayB)

    # Get the diff between arrayA and arrayB by XORing them. Return type: int
    @staticmethod
    def GetDiff_XOR(arrayA, arrayB):
        # black = 0
        xorMatrix = numpy.bitwise_xor(arrayA,arrayB)
        # Util.ArrayToImg(xorMatrix, "GetXOrArray.png")

        return numpy.count_nonzero(xorMatrix)

        # for pixel in numpy.nditer(xorMatrix):
        #     if pixel != 0: black+=1
        # print("XOR Black Count: ", black)
        # return black

    # Get diff between 2 img arrays from the img names. Return type: int
    def GetDiffByImgName(self,img1, img2):
        frame1 = self.GetFrameByName(img1)
        frame2 = self.GetFrameByName(img2)
        diffMatrix =  abs(frame1.imgArray - frame2.imgArray)
        # diffPixelCount = 0

        return numpy.count_nonzero(diffMatrix)

        # Get the diff pixel count using nditer
        # for pixel in numpy.nditer(diffMatrix):
        #     if pixel != 0: diffPixelCount+=1
        # return diffPixelCount

    # Get diff between 2 img arrays from 2 RPM_Frames. Return type: int
    def GetDiffByFrame(self,frameA, frameB):
        diffMatrix =  abs(frameA.imgArray - frameB.imgArray)

        return numpy.count_nonzero(diffMatrix)

        # Get the diff pixel count using nditer
        # for pixel in numpy.nditer(diffMatrix):
        #     if pixel != 0: diffPixelCount+=1
        # return diffPixelCount

    # Return the operator such that Operator(A,B) = C
    @staticmethod
    def GetBestMatchedOperator(allFrames):
        print("\nOutput from GetBestMatchedOperator()")
        print("\n--------------------------------------------------------------------------------")
        frameA = RPM_Solver.GetFrameFromList("A.png", allFrames)
        frameB = RPM_Solver.GetFrameFromList("B.png", allFrames)
        frameC = RPM_Solver.GetFrameFromList("C.png", allFrames)

        frameG = RPM_Solver.GetFrameFromList("G.png", allFrames)
        frameH = RPM_Solver.GetFrameFromList("H.png", allFrames)

        imgArrayA_OR = RPM_Solver.GetORImgArray(frameA.imgArray, frameB.imgArray)
        imgArrayA_XOR = RPM_Solver.GetXORImgArray(frameA.imgArray, frameB.imgArray)
        imgArrayA_AND = RPM_Solver.GetANDImgArray(frameA.imgArray, frameB.imgArray)

        # Store all the diffs between transposed frameA and related frame.
        tempDict = {}
        tempDict["OR"] = RPM_Solver.GetDiff(imgArrayA_OR, frameC.imgArray)
        tempDict["XOR"] = RPM_Solver.GetDiff(imgArrayA_XOR, frameC.imgArray)
        tempDict["AND"] = RPM_Solver.GetDiff(imgArrayA_AND, frameC.imgArray)

        print("Diff frameA and related frame: ", tempDict)
        # Return the operator method that resulted in the smallest diff between Operator(frameA,relatedFrame) and frame3
        bestOperator = str(min(tempDict, key=tempDict.get))
        if (bestOperator == "XOR" and tempDict["OR"] == tempDict["XOR"]):
            bestOperator = "OR"

        answerFrame = RPM_Frame("answer")
        # Apply the best operator to frames G and H, and store it to answerFrame
        if (bestOperator == "OR"):
            answerFrame.imgArray = RPM_Solver.GetORImgArray(frameG.imgArray, frameH.imgArray)
        elif (bestOperator == "XOR"):
            answerFrame.imgArray = RPM_Solver.GetXORImgArray(frameG.imgArray, frameH.imgArray)
        elif (bestOperator == "AND"):
            answerFrame.imgArray = RPM_Solver.GetANDImgArray(frameG.imgArray, frameH.imgArray)

        print("Operator found: ", bestOperator)
        print("\n--------------------------------------------------------------------------------")
        Util.ArrayToImg(answerFrame.imgArray, "Processed_Operator.png")
        return answerFrame

    
#---------------------------------------------#
# This class represents each frame in the RPM #
#---------------------------------------------#

class RPM_Frame:
    def __init__(self, fileName):
        self.fileName = fileName
        self.frameName = ""
        self.components = 0
        self.imgArray = numpy.zeros([184,184],dtype=numpy.uint8)
        self.imgComponentArray = numpy.zeros([184,184],dtype=numpy.uint8)

    # Returns an array of different img component arrays of an image. Also indicates
    # which one is on the left, and which one is on the right. 
    # ONLY WORKS (CORRECTLY) FOR IMAGES WITH 2 COMPONENTS
    def GetSeparateComponents(self):
        components = []
        tempReturnArray = [] 
        returnArray = []
        for pixel in numpy.nditer(self.imgComponentArray):
            if pixel != 0 and pixel not in components: components.append(pixel)
        # print("Components: ", components)
        for comp in components:
            tempArray = copy.deepcopy(self.imgComponentArray)
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

    # Return img array of an img moved by offset from left to right
    @staticmethod
    def MoveLRByOffset(imgArray, offset):
        # indices = numpy.transpose(numpy.nonzero(imgArray))
        return numpy.roll(imgArray,offset)

    # Get LR move offset between 2 img arrays
    @staticmethod
    def GetMoveOffset(imgArray1, imgArray2):
        index_1 = numpy.transpose(numpy.nonzero(imgArray1))[0]
        index_2 = numpy.transpose(numpy.nonzero(imgArray2))[1]
        # print("index_1: ", numpy.transpose(numpy.nonzero(imgArray1)))
        # print("index_2: ", numpy.transpose(numpy.nonzero(imgArray2)))
        # print("Move offset:", index_2[1] - index_1[1])
        return index_2[1] - index_1[1]

    # Get the 4 quadrants of a frame and return an array containing the 4 2D arrays 
    # representing the 4 quadrants
    def GetQuadrants(self):
        # Quadrants go from left to right, top to bottom
        quadrant_1 = copy.deepcopy(self.imgArray[:92, :92])
        quadrant_2 = copy.deepcopy(self.imgArray[:92 ,92:183])
        quadrant_3 = copy.deepcopy(self.imgArray[92:183, :92])        
        quadrant_4 = copy.deepcopy(self.imgArray[92:183, 92:183])
        # print(self.frameName)
        # print("quadrant 1: ", Util.GetBlackPixelCount(quadrant_1))
        # print("quadrant 2: ", Util.GetBlackPixelCount(quadrant_2))
        # print("quadrant 3: ", Util.GetBlackPixelCount(quadrant_3))
        # print("quadrant 4: ", Util.GetBlackPixelCount(quadrant_4), "\n")

        # Util.ArrayToImg(quadrant_1,"quad_1.png")
        # Util.ArrayToImg(quadrant_2,"quad_2.png")
        # Util.ArrayToImg(quadrant_3,"quad_3.png")
        # Util.ArrayToImg(quadrant_4,"quad_4.png")
        return [quadrant_1, quadrant_2, quadrant_3, quadrant_4]
    
    def GetLeftMostPixel(self):
        for i in range(len(self.imgArray)):
            for j in range(len(self.imgArray[0])):
                if (self.imgArray[i][j] != 0):
                    return [i,j]
    
    def GetFillLevel(self):
        totalPixels = 184*184
        fill = self.GetBlackPixelCount()*1.0/totalPixels*100
        # print("Fill percentage for frame " + self.frameName + ": ", fill)
        return fill

    @staticmethod
    def GetFilledImgArray(frame):
        imgArray = copy.deepcopy(frame.imgArray)
        compArray = copy.deepcopy(frame.imgComponentArray)
        # Get x and y max values. These will be the bound
        x = 0
        y = 0
        for i in range(len(compArray)):
            for j in range(len(compArray[0])):
                if (compArray[i][j] != 0):
                    if (i > x): x = i
                    if (j > y): y = j

        print("BOUNDS: ", x,y)
        x -= 8
        y -= 8
        # Fill the image
        for i in range(len(imgArray)):
            for j in range(len(imgArray[0])):
                # If we are not at the top row
                if (i > 0 and j > 0):
                    if (imgArray[i][j-1] == 1 and imgArray[i-1][j] == 1):
                        if (i <= x and j <= y):
                            imgArray[i][j] = 1
        # Util.ArrayToImg(imgArray,"Filled.png")
        return imgArray

    '''
        Compare transposedImgArray with each of the choice frame's image array,
        and return the smallest diff
    '''
    @staticmethod
    def GetBestMatchDiff(transposedImgArray, choiceFrames):
        # Store the diff between transposedImgArray and each choiceFrame's img array
        tempDict = {}
        for choice in choiceFrames:
            tempDiff = RPM_Solver.GetDiff(transposedImgArray,choice.imgArray)
            tempDict[choice.frameName] = tempDiff

        # Store the frame's name, and the choice that returns the smallest diff
        smallest = min(tempDict.values())
        for key, value in tempDict.items():
            if (value == smallest): 
                return value

    '''
        This method perform the common transpositions between
        frameA and relatedFrame, say 'X', then perform 'X' transposition
        on frame3 and return it
        - frameA: The top left-most frame in a 2x2 RM
        - relatedFrame: the frame we are finding the relationship between itself and frameA with
        - frame3: the frame we will apply the transpose found to, and use to find the answer
    '''
    @staticmethod
    def GetClosestMatchedTranspose_v2(frameA, relatedFrame, frame3, choiceFrames):
        print("\nOutput from GetClosestMatchedTranspose_v2()")
        print("\n--------------------------------------------------------------------------------")
        imgArray_relatedFrame = relatedFrame.imgArray

        # Get img array for the 2 common transposes: flip LR and flip TB for frame A
        imgArrayA_FlipLR = frameA.GetTransposedImgArray(Image.FLIP_LEFT_RIGHT)
        imgArrayA_FlipTB = frameA.GetTransposedImgArray(Image.FLIP_TOP_BOTTOM)
        imgArrayA_RotateMinus45 = frameA.GetTransposedImgArray(-45)
        imgArrayA_RotateMinus90 = frameA.GetTransposedImgArray(-90)

        # # Get the best match (and its diff) between a
        # diffDict = {}
        # diffDict = RPM_Frame.StoreBestMatchAndDiff(imgArrayA_FlipLR,choiceFrames, diffDict)
        # diffDict = RPM_Frame.StoreBestMatchAndDiff(imgArrayA_FlipTB,choiceFrames, diffDict)
        # diffDict = RPM_Frame.StoreBestMatchAndDiff(imgArrayA_RotateMinus45,choiceFrames, diffDict)
        # diffDict = RPM_Frame.StoreBestMatchAndDiff(imgArrayA_RotateMinus90,choiceFrames, diffDict)

        # Store all the diffs between transposed frameA and related frame.
        tempDict = {}
        tempDict[FLIP_LR] = RPM_Solver.GetDiff(imgArrayA_FlipLR,imgArray_relatedFrame)
        tempDict[FLIP_TB] = RPM_Solver.GetDiff(imgArrayA_FlipTB,imgArray_relatedFrame)
        tempDict[-45] = RPM_Solver.GetDiff(imgArrayA_RotateMinus45,imgArray_relatedFrame)
        tempDict[-90] = RPM_Solver.GetDiff(imgArrayA_RotateMinus90,imgArray_relatedFrame)

        print("Diff frameA and related frame: ", tempDict)

        # Remove the keys whose value is > our tolerance threshold (need to play around with this)
        for key, value in tempDict.items():
            if (value > 2500): # 2500 is our tolerance threshold 
                del tempDict[key]

        print("Diff frameA and related frame AFTER: ", tempDict)

        # If the tempDict is empty after the removal, return frame3 and 'false' (not found, which means all frames might be different!?)
        if (len(tempDict) == 0):
            return[frame3, False]
        else:
            transposeMethod = ""
            # If the smallest transformation's diff is within a threshold (<40), return immediately
            print("tempDict min: ", min(tempDict.values()))
            if min(tempDict.values()) < 40:
                for key,value in tempDict.items():
                    if (value == min(tempDict.values())):
                        transposeMethod = key
                        break
            else:
                # Apply each of the transpose method to frame3, get the frame from choice frames that
                # best match frame3 transposed, and store it into another dict
                transposeAndDiff = {}
                for key in tempDict.keys():
                    transposedArray = frame3.imgArray
                    if (key == FLIP_LR):
                        transposedArray = frame3.GetTransposedImgArray(Image.FLIP_LEFT_RIGHT)
                    elif (key == FLIP_TB):
                        transposedArray = frame3.GetTransposedImgArray(Image.FLIP_TOP_BOTTOM)
                    elif (key == -45):
                        transposedArray = frame3.GetTransposedImgArray(-45)
                    elif (key == -90):
                        transposedArray = frame3.GetTransposedImgArray(90)

                    transposeAndDiff[key] = RPM_Frame.GetBestMatchDiff(transposedArray,choiceFrames)
                print("transposeAndDiff: ", transposeAndDiff)

                # Get the transpose method that yields the smallest diff
                for key, value in transposeAndDiff.items():
                    if (value == min(transposeAndDiff.values())):
                        transposeMethod = key
                        break

            # Apply that transpose method to frame3, and return it
            if (transposeMethod == FLIP_LR):
                frame3.imgArray = frame3.GetTransposedImgArray(Image.FLIP_LEFT_RIGHT)
            elif (transposeMethod == FLIP_TB):
                frame3.imgArray = frame3.GetTransposedImgArray(Image.FLIP_TOP_BOTTOM)
            elif (transposeMethod == -45):
                frame3.imgArray = frame3.GetTransposedImgArray(-45)
            elif (transposeMethod == -90):
                frame3.imgArray = frame3.GetTransposedImgArray(-90)

            print("Transpose method: ", transposeMethod)
            print("\n--------------------------------------------------------------------------------")
            return [frame3,True]

    @staticmethod
    def GetClosestMatchedTranspose(frameA, relatedFrame, frame3, choiceFrames):
        imgArray_relatedFrame = relatedFrame.imgArray

        # Get img array for the 2 common transposes: flip LR and flip TB for frame A
        imgArrayA_FlipLR = frameA.GetTransposedImgArray(Image.FLIP_LEFT_RIGHT)
        imgArrayA_FlipTB = frameA.GetTransposedImgArray(Image.FLIP_TOP_BOTTOM)
        imgArrayA_RotateMinus45 = frameA.GetTransposedImgArray(-45)
        imgArrayA_RotateMinus90 = frameA.GetTransposedImgArray(-90)

        # Store all the diffs between a given frame and all the choices into a dict.
        tempDict = {}
        tempDict[FLIP_LR] = RPM_Solver.GetDiff(imgArrayA_FlipLR,imgArray_relatedFrame)
        tempDict[FLIP_TB] = RPM_Solver.GetDiff(imgArrayA_FlipTB,imgArray_relatedFrame)
        # tempDict["Rotate90"] = RPM_Solver.GetDiff(imgArrayA_Rotate90,imgArray_relatedFrame)
        # tempDict["Rotate180"] = RPM_Solver.GetDiff(imgArrayA_Rotate180,imgArray_relatedFrame)
        # tempDict["Rotate270"] = RPM_Solver.GetDiff(imgArrayA_Rotate270,imgArray_relatedFrame)

        # Using GetDiff()
        # print("FlipLR diff: ",RPM_Solver.GetDiff(imgArrayA_FlipLR,imgArray_relatedFrame))
        # print("FlipTB diff: ",RPM_Solver.GetDiff(imgArrayA_FlipTB,imgArray_relatedFrame))
        # print("RotateMinus45 diff: ",RPM_Solver.GetDiff(imgArrayA_RotateMinus45,imgArray_relatedFrame))
        # print("RotateMinus90 diff: ",RPM_Solver.GetDiff(imgArrayA_RotateMinus90,imgArray_relatedFrame))

        # # Using GetDiff_XOR()
        # print("FlipLR DiffXOR: ",RPM_Solver.GetDiff_XOR(imgArrayA_FlipLR,imgArray_relatedFrame))
        # print("FlipTB DiffXOR: ",RPM_Solver.GetDiff_XOR(imgArrayA_FlipTB,imgArray_relatedFrame))
        # print("RotateMinus45 DiffXOR: ",RPM_Solver.GetDiff_XOR(imgArrayA_RotateMinus45,imgArray_relatedFrame))
        # print("RotateMinus90 DiffXOR: ",RPM_Solver.GetDiff_XOR(imgArrayA_RotateMinus90,imgArray_relatedFrame))

        # print("Rotate270 diff: ",RPM_Solver.GetDiff(imgArrayA_Rotate270,imgArray_relatedFrame))

        # Find the 1st smallest value
        smallest_1 = min(tempDict.values())
        transposeMethod_1 = ""
        for key, value in tempDict.items():
            if (value == smallest_1): 
                transposeMethod_1 = key
                break # stop since we already found

        # Find the 2nd smallest value
        # smallest_2 =  min(tempDict.values())

        # If the difference of 1st smallest and 2nd smallest is within some threshold
        # We need to 
        # if abs(smallest_1 - smallest_2) <= 40:



        transposeMethod = transposeMethod_1

        # Make a copy of frame3's original img array
        frame3_OriginalImgArray = copy.deepcopy(frame3.imgArray)
        
        # print("DiffFrame3_LR", RPM_Solver.GetDiff(tempFrame3.GetTransposedImgArray(Image.FLIP_LEFT_RIGHT),frame3.imgArray))
        # print("DiffFrame3_TB", RPM_Solver.GetDiff(tempFrame3.GetTransposedImgArray(Image.FLIP_TOP_BOTTOM),frame3.imgArray))
        # print("DiffFrame3_90", RPM_Solver.GetDiff(tempFrame3.GetTransposedImgArray(Image.ROTATE_90),frame3.imgArray))
        # print("DiffFrame3_180", RPM_Solver.GetDiff(tempFrame3.GetTransposedImgArray(Image.ROTATE_180),frame3.imgArray))

        # Apply the transpose method that results in the smallest difference between frameA and relatedFrame to frame3
        if (transposeMethod == FLIP_LR):
            frame3.imgArray = frame3.GetTransposedImgArray(Image.FLIP_LEFT_RIGHT)
        elif (transposeMethod == FLIP_TB):
            frame3.imgArray = frame3.GetTransposedImgArray(Image.FLIP_TOP_BOTTOM)
        # elif (transposeMethod == ROTATE_90):
        #     frame3.imgArray = frame3.GetTransposedImgArray(Image.ROTATE_90)
        # elif (transposeMethod == ROTATE_180):
        #     frame3.imgArray = frame3.GetTransposedImgArray(Image.ROTATE_180)

        # Make a copy of frame3's first transposed imgArray
        frame3ImgArray_Transpose_1 = copy.deepcopy(frame3.imgArray)

        # Get smallest diff found using the method above
        tempDict = {}
        # Store all the diffs between a given frame and all the choices into a dict.
        for choice in choiceFrames:
            tempDiff = RPM_Solver.GetDiff(frame3.imgArray,choice.imgArray)
            tempDict[choice.frameName] = abs(tempDiff)

        # Get the smallest diff between the transposed image and the predicted answer
        smallest_1 = min(tempDict.values())
        print("Smallest 1: ", smallest_1)
        # If the diff is >= threshold, we attempt the other method
        if (smallest_1 >= ARRAY_DIFF_THRESHOLD):
            frame3.imgArray = copy.deepcopy(frame3_OriginalImgArray) # Restore frame 3's img array
            # Do the other method. If originally we did FLIP_LR, now we do FLIP_TB, and vice versa
            if (transposeMethod == FLIP_LR):
                frame3.imgArray = frame3.GetTransposedImgArray(Image.FLIP_TOP_BOTTOM)
            else:
                frame3.imgArray = frame3.GetTransposedImgArray(Image.FLIP_LEFT_RIGHT)

        tempDict = {}
        # Store all the diffs between a given frame and all the choices into a dict.
        for choice in choiceFrames:
            tempDiff = RPM_Solver.GetDiff(frame3.imgArray,choice.imgArray)
            tempDict[choice.frameName] = abs(tempDiff)

        smallest_2 = min(tempDict.values())
        print("Smallest 2: ", smallest_2)

        # If the 2nd diff we found ended up being larger than the first, resotre frame3's image array to
        # that of the first transpose method
        if (smallest_2 > smallest_1):
            frame3.imgArray = copy.deepcopy(frame3ImgArray_Transpose_1)

        return frame3

    def SaveTransposedImg(self,transposeMethod):
        # Open the img and transpose it
        img = Image.open(self.fileName).convert("L")
        if (transposeMethod == Image.FLIP_LEFT_RIGHT):
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        elif (transposeMethod == Image.FLIP_TOP_BOTTOM):
            img = img.transpose(Image.FLIP_TOP_BOTTOM)
        elif (transposeMethod == Image.ROTATE_90):
            img = img.transpose(Image.ROTATE_90)
        elif (transposeMethod == Image.ROTATE_180):
            img = img.transpose(Image.ROTATE_180)
        elif (transposeMethod == 45):
            img = img.rotate(45)
        elif (transposeMethod == -45):
            img = img.rotate(-45)
        elif (transposeMethod == 90):
            img = img.rotate(90)
        elif (transposeMethod == -90):
            img = img.rotate(-90)
        img.save("Transposed.png")

    def GetTransposedImgArray(self, transposeMethod):
        MASK_VALUE = 7 # arbitrary value to convert black pixels to
        BLACK_PIXEL_THRESHOLD = 10
        nonNumberTransposes = [Image.FLIP_LEFT_RIGHT, Image.FLIP_TOP_BOTTOM, Image.ROTATE_90, Image.ROTATE_180, Image.ROTATE_270]
        img = Image.open(self.fileName).convert("L")
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

    def GetBlackPixelCount(self):
        return numpy.count_nonzero(self.imgArray)

        # OLD CODE
        # count = 0
        # for pixel in numpy.nditer(self.imgArray):
        #     if pixel != 0: count+=1
        

    def GetFrameName(self):
        self.frameName = self.fileName.split("\\")[len(self.fileName.split("\\")) - 1]

    def GetComponents(self):
        # Numpy.unique will returns all unique elements in the array including 0, so we have to do '-1' 
        # to get the correct number of components
        self.components =  len(numpy.unique(self.imgComponentArray)) - 1

        # OLD CODE
        # component = []
        # for pixel in numpy.nditer(self.imgComponentArray):
        #     if pixel != 0 and pixel not in component:
        #         component.append(pixel)

        # for i in range(len(self.imgComponentArray)):
        #     for j in range(len(self.imgComponentArray[0])):
        #         if not(self.imgComponentArray[i][j] in component) and self.imgComponentArray[i][j] != 0: 
        #             component.append(self.imgComponentArray[i][j])

        # Testing code
        # unique = numpy.unique(self.imgComponentArray)
        # print("Unique labels: ", unique)
        # print("Len: ", len(unique))

        

    def GetBWImageArray(self,threshold=10): # threshold of 100 works for Basic C-05
        img = Image.open(self.fileName).convert("L") # "L" = black and white mode
        # numpy_array = numpy.array(img)
        numpy_array = numpy.asarray(img,dtype=numpy.uint8)
        numpy.copyto(self.imgArray,numpy_array)
        self.imgArray[self.imgArray <= threshold] = 1
        self.imgArray[self.imgArray > threshold] = 0

        # Original convert method
        # Convert non 0 values to 1
        # for i in range(len(self.imgArray)):
        #     for j in range(len(self.imgArray[0])):
        #         # 255 is white and 0 is black from the original image array
        #         # self.imgArray[i][j] = 0 if self.imgArray[i][j] >= threshold else 1 
        #         # self.imgArray[i][j] = 1 if self.imgArray[i][j] == 0 else 0
        #         self.imgArray[i][j] = 1 if self.imgArray[i][j] <= threshold else 0

        

    def LabelComponents(self):
        currentLabel = 1
        equivDict = {}
        components = 0
        numpy.copyto(self.imgComponentArray,self.imgArray)
        # First scan: Assign component label(s)
        for i in range(len(self.imgComponentArray)):
            for j in range(len(self.imgComponentArray[0])):
                if (self.imgComponentArray[i][j] != 0): # if a node is not a blank space
                    if (j > 0): # If node NOT on the first column
                        
                        # Check left adjacent node
                        if (self.imgComponentArray[i][j-1] == 0): # if left adjacent node == empty

                            # Check for top adjacent node 
                            if (i > 0 and self.imgComponentArray[i-1][j] != 0): # if top adjacent node != empty
                                self.imgComponentArray[i][j] = self.imgComponentArray[i-1][j]
                            
                            # If top and left adjacent nodes are both empty, assign a new component label
                            else:
                                self.imgComponentArray[i][j] = currentLabel
                                currentLabel+=1 # create label for the next component

                                # Increase the number of component found
                                components+=1
                            
                        else: # if left adjacent node != empty, assign it the same value as that node
                            self.imgComponentArray[i][j] = self.imgComponentArray[i][j-1]

                            # Also check if top adjacent node != empty. If so, store equivalency
                            if (i > 0 and self.imgComponentArray[i-1][j] != 0 and self.imgComponentArray[i-1][j] != self.imgComponentArray[i][j-1]):
                                # Compare the 2 pixels that are adjacent to the current pixel. 
                                # The current pixel will get the smaller value
                                if (self.imgComponentArray[i-1][j] < self.imgComponentArray[i][j-1]):
                                    self.imgComponentArray[i][j] = self.imgComponentArray[i-1][j]

                                # Store equivalency
                                self.StoreEquivalency(equivDict,self.imgComponentArray[i-1][j],self.imgComponentArray[i][j-1])

                    # If node is on first column
                    else:
                        # # If node != empty, assign value
                        # if (self.imgComponentArray[i][j] != 0):
                        
                        # If the top adjacent node != 0, assign its value to current node
                        if (self.imgComponentArray[i-1][j] != 0):
                            self.imgComponentArray[i][j] = self.imgComponentArray[i-1][j]
                        
                        # If not, assign a new label to it
                        else:
                            # If not at the the first row, and if top-right node is not empty
                            if (i > 0 and j < len(self.imgComponentArray[0]) and self.imgComponentArray[i-1][j+1] != 0):
                                self.imgComponentArray[i][j] = self.imgComponentArray[i-1][j+1]
                            # If none of the conditions satisfied, assign a new label
                            else:

                                self.imgComponentArray[i][j] = currentLabel
                                currentLabel+=1
                                # Increase the number of component found
                                components+=1

        # 2nd pass: replace labels based on equivalency list
        equivalencyList = []
        for k in sorted(equivDict.keys(), reverse=True):
            # print("Looking at key: ", k)
            # Store the key as the first value in the current equivalency list
            equivalencyList = [k] 
            
            # Add all the values of that key into the same list
            for v in equivDict[k]:
                equivalencyList.append(v)

            # Get the smallest value in equivalencyList, and delete it from equivalencyList
            smallest = min(equivalencyList)
            equivalencyList.remove(smallest)
            
            # Traverse through the imgComponentArray of the current frame. We change all remaining values
            # to 'smallest'
            for v in equivalencyList:
                self.imgComponentArray[self.imgComponentArray == v] = smallest
            # print("Key: ", k, " | Value(s): ", equivDict[k])

            
        # if (self.frameName == "G.png"):
        #     for k in sorted(equivDict.keys(), reverse=True):
        #         print("Key: ", k, " | Values: ", equivDict[k])
        #     temp = []
        #     for pixel in numpy.nditer(self.imgComponentArray):
        #         if (pixel != 0 and pixel not in temp):
        #             print("Value: ", pixel)
        #             temp.append(pixel)
        #     print("Non zero after last pass:", temp)

        
        # 3rd pass: check the labels one more time for equivalencies. Also remove noises from the image
        equivDict = {} # empty equivDict
        iLimit = len(self.imgComponentArray)
        jLimit = len(self.imgComponentArray[0])
        for i in range(len(self.imgComponentArray)):
            for j in range(len(self.imgComponentArray[0])):
                if (self.imgComponentArray[i][j] != 0):
                    # Check top, down, left, and right adjacent pixels. If they are all empty, set that pixel to empty as well
                    checkList = 0
                    if (j + 1 < jLimit and self.imgComponentArray[i][j+1] != 0): # check if right adjacent node is empty
                        checkList+=1
                    if (j - 1 >= 0 and self.imgComponentArray[i][j-1] != 0):  # check if left adjacent node is empty
                        checkList+=1
                    if (i + 1 < iLimit and self.imgComponentArray[i+1][j] != 0): # check if top adjacent node is empty
                        checkList+=1
                    if (i - 1 >= 0 and self.imgComponentArray[i-1][j] != 0): # check if bottom adjacent node is empty
                        checkList+=1
                    # If top,bottom,left, and right adjacent nodes are all empty, we mark that pixel as empty
                    if (checkList == 0):
                        self.imgComponentArray[i][j] = 0
                    
                    # if not, we check for equivalency
                    else:

                        if j > 0: # if the pixel is NOT on the first column, we can check for either top or left equivalencies
                            if i == 0: # if we are on the first row, we can only check for left-adjacent node, NOT top

                                # If we found an equivalency, store it!
                                if self.imgComponentArray[i][j-1] != 0 and self.imgComponentArray[i][j-1] != self.imgComponentArray[i][j]:
                                    # Store equivanlency
                                    self.StoreEquivalency(equivDict,self.imgComponentArray[i][j],self.imgComponentArray[i][j-1])

                            else: # if we are NOT on the first row, we can check for both top and left equivalencies
                                # If we found an equivalency for left adjacent node, store it!
                                if self.imgComponentArray[i][j-1] != 0 and self.imgComponentArray[i][j-1] != self.imgComponentArray[i][j]:
                                    # Store equivanlency
                                    self.StoreEquivalency(equivDict,self.imgComponentArray[i][j],self.imgComponentArray[i][j-1])

                                # If we found an equivalency for top adjacent node, store it!
                                if self.imgComponentArray[i-1][j] != 0 and self.imgComponentArray[i-1][j] != self.imgComponentArray[i][j]:
                                    # Store equivanlency
                                    self.StoreEquivalency(equivDict,self.imgComponentArray[i][j],self.imgComponentArray[i-1][j])

                        else: # if the pixel is on the first column, we only check the top
                            # If we found an equivalency for top adjacent node, store it!
                            if self.imgComponentArray[i-1][j] != 0 and self.imgComponentArray[i-1][j] != self.imgComponentArray[i][j]:
                                # Store equivanlency
                                self.StoreEquivalency(equivDict,self.imgComponentArray[i][j],self.imgComponentArray[i-1][j])
        
        # Replace labels based on equivalency list one more time
        equivalencyList = []
        for k in sorted(equivDict.keys(), reverse=True):
            # print("Looking at key: ", k)
            # Store the key as the first value in the current equivalency list
            equivalencyList = [k] 
            
            # Add all the values of that key into the same list
            for v in equivDict[k]:
                equivalencyList.append(v)

            # Get the smallest value in equivalencyList, and delete it from equivalencyList
            smallest = min(equivalencyList)
            equivalencyList.remove(smallest)
            
            # Traverse through the imgComponentArray of the current frame. We change all remaining values
            # to 'smallest'
            for v in equivalencyList:
                self.imgComponentArray[self.imgComponentArray == v] = smallest
            # print("Key: ", k, " | Value(s): ", equivDict[k])

        # EquivDict after 3rd pass:
        # if (self.frameName == "G.png"):
        #     print("EQUIV_DICT after 3d pass:")
        #     for k in sorted(equivDict.keys(), reverse=True):
        #         print("Key: ", k, " | Values: ", equivDict[k])

        return self.imgComponentArray

    @staticmethod
    def StoreEquivalency(equivDict,keyNode,valueNode):
        # Store equivanlency
        if (keyNode in equivDict):
            if (valueNode not in equivDict[keyNode]):
                equivDict[keyNode].append(valueNode)
        else:
            equivDict[keyNode] = [valueNode]