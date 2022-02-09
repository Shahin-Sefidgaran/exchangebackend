FROM nginx:alpine

RUN rm /etc/nginx/conf.d/default.conf
ADD default.conf /etc/nginx/conf.d/default.conf

RUN mkdir -p /var/www/sigloyex.com/html

COPY ./html/ /var/www/sigloyex.com/html/