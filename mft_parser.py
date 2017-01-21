#-*- coding: utf-8 -*-

import struct
import time

class MFT_reader():

    def __init__(self, dir):

        self.directoryname = dir

    def readRootDir(self): # 처음 루트 디렉토리 부터 읽음.

        self.hVolume = open("\\\\.\\C:", "rb") #볼륨의 핸들을 얻는다.
        self.hVolume.seek(0) # 볼륨의 맨 앞으로 이동!
        vbr = self.hVolume.read(512) # 512바이트를 읽는다.

        if vbr[3:7] == 'NTFS': #볼륨을 제대로 읽었는지 검사
            print "VBR Read Success"

        self.bps = int(struct.unpack("<H", vbr[11:13])[0]) #Bytes per sector
        self.spc = int(struct.unpack("<B", vbr[13])[0]) # Sectors per cluster
        self.cluster = self.bps * self.spc
        startMFTcluster = int(struct.unpack("<Q", vbr[48:56])[0]) #start cluster for $MFT
        self.MFTRecordSize = int(struct.unpack("<B", vbr[64])[0]) # MFT Record 크기 : 필요 없을 수도?
        self.IndexBufSize = int(struct.unpack("<B", vbr[68])[0]) # 폴더 구조에 사용되는 인덱스 버퍼의 크기

        self.MFTEntry0Addr = startMFTcluster * self.cluster
        self.hVolume.seek(self.MFTEntry0Addr + 1024*5)
        self.MFTEntry = self.hVolume.read(1024)

    def readMFTEntry(self):

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

            self.listdirectory(OffsetFileAttr) # 주어진 mft에 대한 index root 를 읽어주는 루틴 호출!

    def listdirectory(self, offset):
        # 디렉토리 안의 목록을 만든다.
        # 여기에서 Index 버퍼를 처리하면서 목록을 만들어 준다?
        # 필요한 부분은 재귀하면서
        # offset은 MFT엔트리의 index root 속성에 대한 시작 오프셋

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
        StartIndxNode = IndxRootHdr + 16

        self.IndexEntrys = self.MFTEntry[StartIndxNode:StartIndxNode + SizeOfContent]

        self.VCNlist = list()
        if not self.IndexEntry():
            print "Index Root Read Success"

        # 자식 노드가 있고, VCN이 있다면 index allocation 속성의 cluster run을 따라가야 한다.
        # VCNlist가 있는 만큼 런 리스트를 따라가야 된다.

        # 다시 시작위치 보정

        EntryEndOffset = IndxRootHdr + SizeOfContent

        if int(struct.unpack("<I", self.MFTEntry[EntryEndOffset:EntryEndOffset+4])[0]) == 160:
            StartIndxAlloc = EntryEndOffset
            NonResidentFlag = int(struct.unpack("B", self.MFTEntry[StartIndxAlloc+8])[0])
            print "[debug:NonResidentFlag]", NonResidentFlag
            LenName = int(struct.unpack("B", self.MFTEntry[StartIndxAlloc+9])[0])
            if NonResidentFlag == 1:
                nonresidentAttrHdr = StartIndxAlloc + 16
                StartVCN = int(struct.unpack("<Q", self.MFTEntry[nonresidentAttrHdr:nonresidentAttrHdr+8])[0])
                EndVCN = int(struct.unpack("<Q", self.MFTEntry[nonresidentAttrHdr+8:nonresidentAttrHdr+16])[0])
                OffsetToRunlist = int(struct.unpack("<H", self.MFTEntry[nonresidentAttrHdr+16:nonresidentAttrHdr+18])[0])

                #TODO : 클러스터 런이 00 일때 그만 읽는 것, VCN
                StartOffsetRunlist = StartIndxAlloc + OffsetToRunlist
                Clen, Coffset = self.ClusterRun(StartOffsetRunlist)
                self.IndexBuffer(Coffset, Clen)

    def IndexBuffer(self, Coffset, Clen):
        self.hVolume.seek(Coffset*self.cluster)
        self.IndexBuf = self.hVolume.read(Clen*self.cluster)
        LenIndexBuf = len(self.IndexBuf)
        RecodeStart = 0
        while True:
            signature = self.IndexBuf[RecodeStart:RecodeStart+4]
            if signature == 'INDX':
                IndexRecordStartVCN = int(struct.unpack("<Q", self.IndexBuf[RecodeStart + 16:RecodeStart + 24])[0])
                print "[debug:IndexRecordStartVCN]", IndexRecordStartVCN
                IndxNodeHdr = RecodeStart + 24

                self.IndexEntrys = self.IndexBuf[IndxNodeHdr:]

                print "[debug:VCNlist]", self.VCNlist
                if IndexRecordStartVCN in self.VCNlist:
                    RecodeStart = self.IndexEntry()
                    print "[debug:RecodeStart]", RecodeStart
                    if RecodeStart == 0:
                        break
                    else:
                        continue


    def ClusterRun(self, offset):
        runlist = hex(struct.unpack("B", self.MFTEntry[offset])[0])
        COffset = int(runlist[2])
        Clen = int(runlist[3])

        Cluster = list()
        for element in self.MFTEntry[offset + 1:offset + 1 + Clen]:
            Cluster.append('{:x}'.format(int(struct.unpack("B", element)[0])))
        Cluster.reverse()
        Clusterlen = "".join(Cluster)
        Clusterlen = int(Clusterlen, 16)

        Cluster = list()
        for element in self.MFTEntry[offset + 1 + Clen:offset + 1 + Clen + COffset]:
            Cluster.append('{:x}'.format(int(struct.unpack("B", element)[0])))
        Cluster.reverse()
        Clusteroffset = "".join(Cluster)
        Clusteroffset = int(Clusteroffset, 16)

        return Clusterlen, Clusteroffset

    def IndexEntry(self):

        # 여기서부턴 상대적 주소로 계산해야됨
        IndxNodeHdr = 0
        # 여기로 점프
        OffsetStartIndxEntry = IndxNodeHdr + int(struct.unpack("<I", self.IndexEntrys[IndxNodeHdr:IndxNodeHdr + 4])[0])
        #이 크기 만큼 읽어야 함
        SizeIndxEntryList = int(struct.unpack("<I", self.IndexEntrys[IndxNodeHdr + 4:IndxNodeHdr + 8])[0])
        print "[debug:SizeIndxEntryList]", SizeIndxEntryList
        # SizeAllocIndxEntryList에서 SizeIndxEntryList를 뺀 만큼이 slack 영역
        SizeAllocIndxEntryList = int(struct.unpack("<I", self.IndexEntrys[IndxNodeHdr +8:IndxNodeHdr +12])[0])
        print "[debug:SizeAllocIndxEntryList]", SizeAllocIndxEntryList
        ChildNodeFlag = int(struct.unpack("<I", self.IndexEntrys[IndxNodeHdr + 12:IndxNodeHdr + 16])[0])

        IndexEntrySlackData = SizeAllocIndxEntryList - SizeIndxEntryList
        print "[debug:IndexEntrySlackData]", IndexEntrySlackData #이만큼 건너뛰어야 한다.

        SizeIndxEntryList = SizeIndxEntryList - 16
        self.EntrySeek = OffsetStartIndxEntry # 초기 설정.
        check = SizeIndxEntryList
        print "[debug:check(1)]", check

        while True:

            # Index Record
            print "====== Index Entry ======"
            FileRef = self.IndexEntrys[self.EntrySeek:self.EntrySeek + 8]
            print "[debug:FileRef]", FileRef
            LenOfEntry = int(struct.unpack("<H", self.IndexEntrys[self.EntrySeek + 8:self.EntrySeek + 10])[0])
            print "[debug:LenOfEntry]", LenOfEntry
            LenOfContent = int(struct.unpack("<H", self.IndexEntrys[self.EntrySeek + 10:self.EntrySeek + 12])[0])
            print "[debug:LenOfContent]", LenOfContent
            Flags = int(struct.unpack("<I", self.IndexEntrys[self.EntrySeek + 12:self.EntrySeek + 16])[0])
            print "[debug:Flags]", Flags

            if LenOfContent > 0:
                OffsetStartFNA = self.EntrySeek + 16
                FNA = self.IndexEntrys[OffsetStartFNA:OffsetStartFNA + LenOfContent]
                self.FileNameAttr(FNA)
                #print "[debug:FNA]", FNA

            self.EntrySeek = self.EntrySeek + LenOfEntry # 하나의 엔트리를 다 읽었으므로 엔트리 끝으로 이동.

            if Flags == 0:
                print "[debug] flag is zero"
                #return

            if Flags == 1: # 자식 노드가 있음.
                OffsetVCN = self.EntrySeek # 맨 끝에서 읽을 꺼니까.
                print "[debug:OffsetVCN]", OffsetVCN
                VCN = int(struct.unpack("<Q", self.IndexEntrys[OffsetVCN - 8:OffsetVCN])[0])
                print "[debug:VCN]", VCN
                self.VCNlist.append(VCN)

            elif Flags == 2: # End of Node
                #End of Node 이후에 나오는 값들은? slack data
                OffsetVCN = self.EntrySeek
                print "[debug:OffsetVCN]", OffsetVCN
                check = LenOfEntry
                return SizeAllocIndxEntryList + 24
                #return 0, OffsetVCN, 0

            elif Flags == 3: # 자식 노드 있음 + End of Node
                OffsetVCN = self.EntrySeek
                print "[debug:OffsetVCN]", OffsetVCN
                VCN = int(struct.unpack("<Q", self.IndexEntrys[OffsetVCN - 8:OffsetVCN])[0])
                print "[debug:VCN]", VCN
                self.VCNlist.append(VCN)

            # 인덱스 엔트리를 전부 읽었는지 검사
            check = check - LenOfEntry
            print "[debug:check]", check
            if check == 0:
                break

        return 0

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

