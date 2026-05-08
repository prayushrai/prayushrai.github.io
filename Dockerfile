# Railway deployment — static site served via nginx.
#
# The whole point of this Dockerfile is to ship the already-built site
# (index.html, dp.jpg) and ignore everything else. The Python build
# pipeline (build_unified.py + the raw CSVs/PDFs) only runs locally to
# regenerate index.html when source data changes — Railway never needs
# to see it.
#
# nginx-alpine's entrypoint auto-runs envsubst on /etc/nginx/templates/*
# at container start, substituting ${PORT} from Railway's runtime env
# while leaving bare $vars (like $uri) alone — that's why we use the
# .template suffix.

FROM nginx:alpine

COPY . /usr/share/nginx/html

RUN rm -f /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/templates/default.conf.template

EXPOSE 8080
