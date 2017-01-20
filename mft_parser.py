#-*- coding: utf-8 -*-

import struct
import time

class MFT_reader():

    def __init__(self, dir):

        self.directoryname = dir

    def readRootDir(self):

        self.hVolume = open("\\\\.\\C:", "rb") #볼륨의 핸들을 얻는다.
        self.hVolume.seek(0) # 볼륨의 맨 앞으로 이동!
        vbr = self.hVolume.read(512) # 512바이트를 읽는다.

        if vbr[3:7] == 'NTFS': #볼륨을 제대로 읽었는지 검사
            print "VBR Read Success"

        self.bps = int(struct.unpack("<H", vbr[11:13])[0]) #Bytes per sector
        self.spc = int(struct.unpack("<B", vbr[13])[0]) # Sectors per cluster
        startMFTcluster = int(struct.unpack("<Q", vbr[48:56])[0]) #start cluster for $MFT
        self.MFTRecordSize = int(struct.unpack("<B", vbr[64])[0]) # MFT Record 크기 : 필요 없을 수도?
        self.IndexBufSize = int(struct.unpack("<B", vbr[68])[0]) # 폴더 구조에 사용되는 인덱스 버퍼의 크기

        self.MFTEntry0Addr = startMFTcluster * self.bps * self.spc
        self.hVolume.seek(self.MFTEntry0Addr + 1024*5)

    def readMFTEntry(self):

        self.MFTEntry = self.hVolume.read(1024)

        if self.MFTEntry[0:4] == 'FILE':
            # Offset to File attribute MFT Record Header에서 첫 번째 속성의 위치 값을 읽음.
            OffsetFileAttr = int(struct.unpack("<H", self.MFTEntry[20:22])[0])

            # 속성 값과 길이 값을 읽으면서, INDEX_ROOT 속성을 찾으면, 스톱
            while True:
                attr_type = int(struct.unpack("<I", self.MFTEntry[OffsetFileAttr:OffsetFileAttr+4])[0])
                if attr_type == 144:
                    break
                attr_len = int(struct.unpack("<I", self.MFTEntry[OffsetFileAttr+4:OffsetFileAttr+8])[0])
                OffsetFileAttr = OffsetFileAttr + attr_len

            self.listdirectory(OffsetFileAttr)

    def listdirectory(self, offset):
        # 디렉토리 안의 목록을 만든다.
        # 여기에서 Index 버퍼를 처리하면서 목록을 만들어 준다?
        # 필요한 부분은 재귀하면서

        # common header 16byte pass
        # $INDEX_ROOT는 resident attribute 이므로
        # Resident Attribute Header가 필요
        residentAttrHdr = offset + 16

        SizeOfContent = int(struct.unpack("<I", self.MFTEntry[residentAttrHdr:residentAttrHdr + 4])[0])
        print "[debug:SizeOfContent]", SizeOfContent
        OffsetToContent = int(struct.unpack("<H", self.MFTEntry[residentAttrHdr + 4:residentAttrHdr + 6])[0])

        # 실제 속성 내용이 시작하는 위치를 찾아갈 수 있음
        # Index Root Header는 지나감, Index Node Header부터 시작
        IndxRootHdr = offset + OffsetToContent
        IndxNodeHdr = IndxRootHdr + 16
        OffsetStartIndxEntry = IndxNodeHdr + (struct.unpack("<I", self.MFTEntry[IndxNodeHdr:IndxNodeHdr + 4])[0])
        SizeIndxEntryList = int(struct.unpack("<I", self.MFTEntry[IndxNodeHdr + 4:IndxNodeHdr + 8])[0])
        ChildNodeFlag = int(struct.unpack("<I", self.MFTEntry[IndxNodeHdr + 12:IndxNodeHdr + 16])[0])

        while True:
            EndOfNode, LOE = self.IndexEntry(OffsetStartIndxEntry)
            if not EndOfNode:
                break
            # 다음 순서로 넘어가야 됨.
            OffsetStartIndxEntry = OffsetStartIndxEntry + LOE



    def IndexEntry(self, offset):
        # Index Record
        print "====== Index Entry ======"
        FileRef = self.MFTEntry[offset:offset + 8]
        print "[debug:FileRef]", FileRef
        LenOfEntry = int(struct.unpack("<H", self.MFTEntry[offset + 8:offset + 10])[0])
        print "[debug:LenOfEntry]", LenOfEntry
        LenOfContent = int(struct.unpack("<H", self.MFTEntry[offset + 10:offset + 12])[0])
        print "[debug:LenOfContent]", LenOfContent
        Flags = int(struct.unpack("<I", self.MFTEntry[offset + 12:offset + 16])[0])
        print "[debug:Flags]", Flags

        if LenOfContent > 0:
            OffsetStartFNA = offset + 16
            FNA = self.MFTEntry[OffsetStartFNA:OffsetStartFNA + LenOfContent]
            self.FileNameAttr(FNA)
            #print "[debug:FNA]", FNA

        if Flags == 1: # 자식 노드가 있음.
            OffsetVCN = offset + LenOfEntry
            print "[debug:OffsetVCN]", OffsetVCN
            VCN = int(struct.unpack("<Q", self.MFTEntry[OffsetVCN - 8:OffsetVCN])[0])
            print "[debug:VCN]", VCN
            return 1, LenOfEntry

        elif Flags == 2: # End of Node
            return 0, 0

        elif Flags == 3: # 자식 노드 있음 + End of Node
            OffsetVCN = offset + LenOfEntry
            print "[debug:OffsetVCN]", OffsetVCN
            VCN = int(struct.unpack("<Q", self.MFTEntry[OffsetVCN - 8:OffsetVCN])[0])
            print "[debug:VCN]", VCN
            return 0, 0

    def FileNameAttr(self, FNAdata):
        print "====== FileName Attribute ======"
        FileRef = int(struct.unpack("<Q", FNAdata[0:8])[0]) # 앞의 6바이트는 MFT
        CreateTime = int(struct.unpack("<Q", FNAdata[8:16])[0])
        ModifiedTime = int(struct.unpack("<Q", FNAdata[16:24])[0])
        MFTModifiedTime = int(struct.unpack("<Q", FNAdata[24:32])[0])
        LastAccessedTime = int(struct.unpack("<Q", FNAdata[32:40])[0])
        RealSizeoffile = FNAdata[48:56]
        Flags = FNAdata[56:60]
        LenName = int(struct.unpack("B", FNAdata[64])[0])
        Namespace = int(struct.unpack("B", FNAdata[65])[0])
        FileName = FNAdata[66:66+LenName*2]
        print "[debug:FileName]", FileName
        print "================================"


test = MFT_reader("dir")
test.readRootDir()
test.readMFTEntry()
