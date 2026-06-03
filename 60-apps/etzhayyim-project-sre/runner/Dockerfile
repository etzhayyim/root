FROM mcr.microsoft.com/playwright:v1.50.0-jammy

WORKDIR /app

COPY package.json ./
RUN npm install

# Install Playwright browsers
RUN npx playwright install chromium --with-deps

COPY . .

ENV SRE_BASE_URL=https://sre.etzhayyim.com
ENV SRE_ACCESS_TOKEN=""

CMD ["npx", "ts-node", "run.ts"]
