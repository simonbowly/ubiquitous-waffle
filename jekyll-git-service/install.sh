cp jekylld-restart-serve.sh jekylld-start.sh jekylld-stop.sh /usr/local/bin/
cp jekylld.service /etc/systemd/system/
systemctl daemon-reload
