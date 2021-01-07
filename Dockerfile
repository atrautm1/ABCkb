FROM python:slim

LABEL version="skinny"
# So python yields all output..
ENV PYTHONUNBUFFERED=1
# Copy all scripts to the /app directory
COPY scripts /app/scripts

COPY abckb-browser /app/abckb-browser
# Install required modules
RUN bash /app/scripts/install_packages.sh