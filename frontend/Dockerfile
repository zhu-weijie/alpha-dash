# frontend/Dockerfile
FROM node:22-alpine

WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock)
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Expose the port React app runs on
EXPOSE 3000

# Command to start the React development server
CMD ["npm", "start"]
