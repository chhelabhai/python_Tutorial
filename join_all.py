#! /usr/bin/env python

import sys
import time
import csv
import argparse

def loadCSVFile(file_name,header=False,DELIM="|",QUOTECHAR='"'):
    
    f = open(file_name,"r")
    csvReader = csv.reader(f, delimiter=DELIM, quotechar=QUOTECHAR)
    
    if header:
        headerLine = next(csvReader)

    data = []
    for row in csvReader:
        data.append(row)

    f.close()

    if header:
        return headerLine, data
    else:
        return data
    
# pk is Primary Key
def metaLoadCSVFile(file_name,pk):
    header, data = loadCSVFile(file_name, header=True, DELIM=",")

    if pk not in header:
        raise ValueError("Error: primary key (%s) not in header line of %s" % (pk, fn))
    
    # Find the index of the primary key column
    pkIndex = header.index(pk)

    # Make sure that our primary key column has all unique values
    pkSet = set()
    for row in data:
        if row[pkIndex] in pkSet:
            raise ValueError("Error: primary key column is not unique in %s (duplicate value found: %s)" % (file_name, row[pkIndex]))
        else:
            pkSet.add(row[pkIndex])

    return header, data, pkIndex

def doArgs(argList, name):
    parser = argparse.ArgumentParser(description=name)

    parser.add_argument("-v", "--verbose", action="store_true", help="Show output from latex and dvipng commands", default=False)
    parser.add_argument("leftFilename", type=str, help="Filename of left table")
    parser.add_argument("leftPK", type=str, help="Name of column to use as the primary key for the left table")
    parser.add_argument("rightFilename", type=str, help="Filename of the right table")
    parser.add_argument("rightPK", type=str, help="Name of column to use as the primary key for the right table")
    parser.add_argument("outputFilename", type=str, help="Output filename")
    parser.add_argument("-t", "--type",  type=str, action="store", dest="joinType", choices=["left","right","inner","full"], help="Type of join (default is 'left join')", default="left")

    return parser.parse_args(argList)

def main():

    args = doArgs(sys.argv[1:], "CSV join script")
    startTime = float(time.time())

    #-------------------------------------------------------------------------------------------
    # Load the left data file
    #-------------------------------------------------------------------------------------------
    leftFilename = args.leftFilename
    leftPK = args.leftPK

    leftHeader, leftData, leftKeyIndex = metaLoadCSVFile(leftFilename, leftPK)

    # Map the primary keys to their row index so we can look up keys from the other table in constant time
    leftPKMap = {}
    for i,row in enumerate(leftData):
        leftPKMap[row[leftKeyIndex]] = i

    #-------------------------------------------------------------------------------------------
    # Load the right data file
    #-------------------------------------------------------------------------------------------
    rightFn = args.rightFn
    rightPK = args.rightPK

    rightHeader, rightData, rightKeyIndex = metaLoadCSVFile(rightFilename, rightPK)

    # Map the primary keys to their row index so we can look up keys from the other table in constant time
    rightPKMap = {}
    for i,row in enumerate(rightData):
        rightPKMap[row[rightKeyIndex]] = i

    #-------------------------------------------------------------------------------------------
    # Write output file
    #-------------------------------------------------------------------------------------------
    outputFn = args.outputFn
    joinType = args.joinType

    f = open(outputFilename, 'w')
    csvWriter = csv.writer(f, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csvWriter.writerow(leftHeader + rightHeader)

    #-------------------------------------------------------------------------------------------
    if joinType == "left":

        # Iterate through each row in the left table, try to find the matching row in the right table
        # if the matching row doesn't exist, then fill with 'null's, if it does, then copy it over
        for leftRow in leftData:
            leftRowPK = leftRow[leftKeyIndex]
            rightRow = None
            if leftRowPK in rightPKMap:
                rightRow = rightData[rightPKMap[leftRowPK]]
            else:
                rightRow = ["null"] * len(rightHeader)

            csvWriter.writerow(leftRow + rightRow)
    #-------------------------------------------------------------------------------------------
    elif joinType == "right":

        # Similar to 'left' case
        for rightRow in rightData:
            rightRowPK = rightRow[rightKeyIndex]
            leftRow = None
            if rightRowPK in leftPKMap:
                leftRow = leftData[leftPKMap[rightRowPK]]
            else:
                leftRow = ["null"] * len(leftHeader)

            csvWriter.writerow(leftRow + rightRow)
    #-------------------------------------------------------------------------------------------
    elif joinType == "inner":
        # This join will only write rows for primary keys in the intersection of the two primary key sets
        leftKeySet = set(leftPKMap.keys())
        rightKeySet = set(rightPKMap.keys())

        newKeys = leftKeySet & rightKeySet

        for keyVal in newKeys:
            leftRow = leftData[leftPKMap[keyVal]]
            rightRow = rightData[rightPKMap[keyVal]]

            csvWriter.writerow(leftRow + rightRow)
    #-------------------------------------------------------------------------------------------
    elif joinType == "full":
        # This join will only write rows for primary keys in the union of the two primary key sets
        leftKeySet = set(leftPKMap.keys())
        rightKeySet = set(rightPKMap.keys())

        newKeys = leftKeySet | rightKeySet

        for keyVal in newKeys:
            leftRow = None
            if keyVal in leftPKMap:
                leftRow = leftData[leftPKMap[keyVal]]
            else:
                leftRow = ["null"] * len(leftHeader)
            
            rightRow = None
            if keyVal in rightPKMap:
                rightRow = rightData[rightPKMap[keyVal]]
            else:
                rightRow = ["null"] * len(rightHeader)

            csvWriter.writerow(leftRow + rightRow)
    #-------------------------------------------------------------------------------------------
    else:
        raise Exception("This shouldn't happen")

    f.close()

    print "Finished in %0.4f seconds" % (time.time() - startTime)


if __name__ == "__main__":
    main()
