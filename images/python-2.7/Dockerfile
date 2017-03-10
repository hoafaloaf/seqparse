FROM python:2.7
MAINTAINER Geoff Harvey <hoafaloaf@gmail.com>

RUN pip install \
    ansible \
    coverage \
    mock \
    nose \
    pylint \
    scandir

ADD helloworld.yml /tmp/.

# Default command
CMD ["/bin/bash"]
