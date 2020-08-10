for f in ./*.zwospec; do
    python3 ../zwomaker.py -s $f -m ../messages.zwodef -o $(echo $f | sed s/zwospec/zwo/)
done