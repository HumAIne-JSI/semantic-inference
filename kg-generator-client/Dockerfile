# Use an official Node.js runtime as a parent image
FROM node:14-alpine

COPY * .

RUN npm install

COPY . .

RUN npm run build

EXPOSE 3000

# Define the command to run the app
CMD ["npm", "start"]
