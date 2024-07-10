import pygame
pygame.mixer.init()
# pygame.mixer.music.load("D:\\FireDetection\\FireSmokeDetection\\need\\JingBao\\JIngBaoYin.mp3")
pygame.mixer.music.load("need/JingBao/JIngBaoYin.mp3")

isflag=False

def playAudio():
    if isflag:
        pygame.mixer.music.play()

def setIsFlasg():
    global isflag
    if isflag:
        isflag=False
    else:
        isflag=True
# import playsound
#
# isflag = False
#
# def playAudio():
#     if isflag:
#         playsound("D:\\FireDetection\\FireSmokeDetection\\need\\JingBao\\JIngBaoYin.mp3")
#
# def setIsFlasg():
#     global isflag
#     if isflag:
#         isflag = False
#     else:
#         isflag = True
