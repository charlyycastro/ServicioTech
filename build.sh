cat > build.sh << 'EOF'
#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
EOF

chmod +x build.sh
git add build.sh
git commit -m "Add build.sh for Render"
git push
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate