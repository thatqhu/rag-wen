FROM node:18-alpine
WORKDIR /workspace/frontend
COPY package*.json ./
RUN npm install
CMD ["npm", "run", "dev", "--", "--host"]
