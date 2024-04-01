# Use an official Node.js runtime as a parent image
FROM node:14-alpine

COPY * .

RUN npm install

COPY . .

RUN npm run build

RUN npm -g install serve

EXPOSE 3000

# Define the command to run the app
CMD ["serve", "-s", "build"]
