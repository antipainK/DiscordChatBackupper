consoleWidth = 80
tabWidth = 4
previousLines = {"#": "################################################################################"}

def createCharLine(character):  # full line width
    try:
        return previousLines[character]
    except KeyError:
        previousLines[character] = createCharLineWithLength(character, consoleWidth)
        return previousLines[character]


def createCharLineWithLength(character, length=consoleWidth):
    output = character
    yetToWrite = length - 1
    alreadyWritten = 1
    while(yetToWrite > 0):
        if(yetToWrite >= alreadyWritten):
            output += output
            yetToWrite -= alreadyWritten
            alreadyWritten *= 2
        else:
            temp = createCharLineWithLength(character, yetToWrite)
            output += temp
            alreadyWritten += yetToWrite
            yetToWrite = 0
    return output


def createTabbed(text, amountOfTabs=1):
    return createCharLineWithLength(" ", tabWidth * amountOfTabs) + text


def createCentered(text):
    if(len(text) > consoleWidth):
        return createTabbed(text)
    else:
        return createCharLineWithLength(" ", int((consoleWidth-len(text))/2)) + text

def createNewLines(amount=1):
    output = "\n"
    yetToWrite = amount - 1
    alreadyWritten = 1
    while(yetToWrite > 0):
        if(yetToWrite >= alreadyWritten):
            output += output
            yetToWrite -= alreadyWritten
            alreadyWritten *= 2
        else:
            temp = createNewLines(yetToWrite)
            output += temp
            alreadyWritten += yetToWrite
            yetToWrite = 0
    return output

def printCharLine(character, newLine=True):
    if(newLine):
        print(createCharLine(character))
    else:
        print(createCharLine(character), end='')

def printTabbed(text, amountOfTabs=1, newLine=True):
    if(newLine):
        print(createTabbed(text, amountOfTabs))
    else:
        print(createTabbed(text, amountOfTabs), end='')

def printCentered(text, newLine=True):
    if(newLine):
        print(createCentered(text))
    else:
        print(createCentered(text), end='')

def printNewLines(amount):
    print(createNewLines(amount), end='')


def printMessage(text):
    output = createCharLine("#") + createNewLines(2) + createCentered(text) + createNewLines(2) + createCharLine("#")
    print(output)


def printLesserMessage(text):
    output = createCharLine("-") + createNewLines() + createTabbed(text) + createNewLines() + createCharLine("-")
    print(output)
