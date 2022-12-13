FROM registry.access.redhat.com/ubi8/ubi

WORKDIR /

COPY requirements.txt .
COPY run.py .
COPY config.yaml .
COPY company_credit_data.csv .

RUN yum clean all

RUN yum install -y -q python39 gcc python39-devel
RUN python3.9 -m pip install -r requirements.txt

EXPOSE 9101

CMD ["python3.9", "run.py"]