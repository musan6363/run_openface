'''
任意の動画ファイル，フォルダを引数に渡してOpenFaceを実行するプログラム
https://scrapbox.io/cmc/run_openface
python main.py <input_dir> <output_dir(opt)>
デフォルトではカレントディレクトリに出力
'''

import sys
import os
from pathlib import Path
import datetime
import glob
import subprocess
import shutil

# 定数
IS_VIDEO_FILE = 0
IS_DIR = 1
SUFFIXS = ['.mp4', '.MP4', '.avi', '.AVI', '.mov', '.MOV']
CMD = r"/home/mrkm/openface/OpenFace/build/bin/FaceLandmarkVidMulti"  # 実行するコマンドのパス

class RunOpenFace:
    def __init__(self):
        self.checkargs()
        self._filepath = Path(sys.argv[1])
        self.videos = []
    
    def run(self):
        self.flag = self._is_file_exist()
        self._mkdir()
        self._video_extract()
        self._exec_openface_cmd()
        self._remove_tmp_files()


    def checkargs(self):
        if len(sys.argv) < 2:
            print("hint) python main.py <input_dir> <output_dir(opt)>")
            sys.exit(1)
        
        # 出力ディレクトリの指定
        # dt_now = datetime.datetime.now()
        # now = dt_now.strftime('%Y-%m-%d--%H-%M-%S')  # 2021-10-05--17-35-12
        # outdir = f"processed_{now}"
        # if len(args) > 2:
        #     outdir = args[2]
        
        # self.outdir = outdir

    def _is_file_exist(self):
        if self._filepath is None:
            print("NONE")
            return -1
        elif self._filepath.is_file():
            # ファイルは動画か判定する
            ext = self._filepath.suffix
            if ext in SUFFIXS:
                return IS_VIDEO_FILE
            else:
                self.label_text = self._filepath.name + " is not Video"
                return -1
        elif self._filepath.is_dir():
            return IS_DIR
        else:
            print("ERROR")
            return -1

    def _mkdir(self):
        _dt_now = datetime.datetime.now()
        _now = _dt_now.strftime('%Y-%m-%d--%H-%M-%S')  # 2021-10-05--17-35-12
        _outdirname = f"processed_{_now}"
        _new_dir_path = Path(_outdirname)
        self.lastpath = os.path.splitext(os.path.basename(str(_new_dir_path)))[0]
        self.pare_name = str(_new_dir_path.parent)
        self.outdir = self.pare_name + f"/tmp_{self.lastpath}_output/"  # 処理終了後にtmpを消す
        self.csvdir = Path(self.outdir + "csv/")  # 全てのCSVをまとめる
        try:
            os.makedirs(self.csvdir)
        except FileExistsError:
            pass
        # glaphdir = Path(outdir + "glaph/")
        # try:
        #     os.makedirs(glaphdir)
        # except FileExistsError:
        #     pass

    def _video_extract(self):
        if self.flag == IS_VIDEO_FILE:
            self.videos.append(str(self._filepath))
        elif self.flag == IS_DIR:
            for filetype in SUFFIXS:
                # 動画だけを対象に追加
                self.videos.extend(glob.glob(str(self._filepath) + "/*" + filetype))
        else:
            self.label_text = "ファイルが見つかりません"
            return

    def _exec_openface_cmd(self):
        _runcount = 1
        for inputvideo in self.videos:
            target_path = Path(inputvideo)
            video_name = target_path.stem

            _dt_now = datetime.datetime.now()
            _now = _dt_now.strftime('%Y/%m/%d %H:%M:%S')
            print(f"{_now} \t [{_runcount}/{len(self.videos)}]\t" + video_name + "\tis Running")
            _runcount += 1
            # 実行中のファイルを記録．異常終了時に確認する用．正常終了すればこのファイルは消える．
            with open(self.outdir + "run_time.txt", mode='a') as run_f:
                run_f.write(_now + "\t" + video_name + '\n')

            # try:  # 既知のエラーがいくつか出始めたらtry文を使う
            # 【メイン】OpenFaceの実行
            result = subprocess.run([CMD, "-f", target_path, "-out_dir", self.outdir + video_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # OpenFace実行結果の確認
            with open(self.outdir + video_name + "/" + video_name + "_stdout.txt", mode='w') as stdout_f:
                stdout_f.write(result.stdout)

            # if result.stderr and result.stderr not in ignore_error:
            if result.stderr:
                # エラー出力があれば各ディレクトリにログを残す．
                # 出力ディレクトリにエラーが出たファイル名をまとめて追記する．
                self.flag_error = True
                with open(self.outdir + video_name + "/" + video_name + "_stderr.txt", mode='w') as stderr_f:
                    stderr_f.write(result.stderr + '\n')
                with open(self.outdir + "stderr_all.txt", mode='a') as allerr_f:
                    allerr_f.write(video_name + '\n')

            if result.returncode == 0:
                ori_csv = Path(self.outdir + video_name + "/" + video_name + ".csv")
                shutil.copy(ori_csv, self.csvdir)
            else:
                print("error " + video_name)
            # except:
            #     エラーが見つかったとき用
            #     self.flag_error = True
            #     print(video_name + "\tUnexpected Error" + '\n')
            #     with open(self.outdir + video_name + "/" + video_name + "_stderr.txt", mode='a') as stderr_f:
            #         stderr_f.write("Unexpected Error\n")
            #     with open(self.outdir + "stderr_all.txt", mode='a') as allerr_f:
            #         allerr_f.write(video_name + "\tUnexpected Error" + '\n')
        self._filepath = None

    def _remove_tmp_files(self):
        # exec_openface_cmdでtry文を有効にしたとき，コメントアウトの解除
        # if not self.flag_error:
        #     new_dir = self.pare_name + f"/{self.lastpath}_output/"
        #     os.rename(self.outdir[:-1], new_dir)  # フォルダのリネーム
        # else:
        #     print(f"Error\ndetail -> {self.outdir}/stderr_all.txt")
        _ = subprocess.run(["tar", "-cvf", f"{self.csvdir}.tar.gz", self.csvdir], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        new_dir = self.pare_name + f"/{self.lastpath}_output/"
        os.rename(self.outdir[:-1], new_dir)  # フォルダのリネーム
        

if __name__ == '__main__':
    RunOpenFace().run()

