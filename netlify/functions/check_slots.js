const chromium = require('chrome-aws-lambda');
const nodemailer = require('nodemailer');

// Configuration
const TARGET_DATES = ['2025-05-17', '2025-05-18'];
const TIME_RANGE = {
  start: '12:00',
  end: '21:00'
};
const BOOKING_URL = 'https://www.tablecheck.com/en/shops/pizza-4ps-in-indiranagar/reserve';
const USER_EMAIL = 'aadarshgupta1412@gmail.com';
const BOOKING_INFO = {
  name: 'Aadarsh Gupta',
  phone: '917879974479',
  adults: [4, 3, 2]
};

async function sendEmail(subject, message) {
  const transporter = nodemailer.createTransport({
    host: 'smtp.gmail.com',
    port: 587,
    secure: false,
    auth: {
      user: process.env.EMAIL_USER,
      pass: process.env.EMAIL_PASSWORD
    }
  });

  await transporter.sendMail({
    from: process.env.EMAIL_USER,
    to: USER_EMAIL,
    subject: subject,
    text: message
  });
}

async function checkAvailability() {
  let browser = null;
  
  try {
    browser = await chromium.puppeteer.launch({
      args: chromium.args,
      defaultViewport: chromium.defaultViewport,
      executablePath: await chromium.executablePath,
      headless: true,
    });

    const page = await browser.newPage();
    await page.goto(BOOKING_URL, { waitUntil: 'networkidle0' });

    for (const date of TARGET_DATES) {
      for (const numAdults of BOOKING_INFO.adults) {
        try {
          // Select date
          await page.type('[data-testid="date-picker-input"]', date);
          
          // Wait for time slots to load
          await page.waitForSelector('.time-slot', { timeout: 5000 });
          
          // Get available time slots
          const slots = await page.evaluate(() => {
            const elements = document.querySelectorAll('.time-slot');
            return Array.from(elements).map(el => el.textContent.trim());
          });

          const availableSlots = slots.filter(slot => {
            const time = slot.split(' ')[0];
            return time >= TIME_RANGE.start && time <= TIME_RANGE.end;
          });

          if (availableSlots.length > 0) {
            const message = `Found slots for ${date} with ${numAdults} adults:\n${availableSlots.join('\n')}`;
            await sendEmail('Pizza 4P\'s Slots Available!', message);
            console.log(message);
          }
        } catch (error) {
          console.error(`Error checking ${date} for ${numAdults} adults:`, error);
        }
      }
    }
  } catch (error) {
    console.error('Error:', error);
    await sendEmail('Pizza 4P\'s Slot Checker Error', error.toString());
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

// Schedule the function to run every 30 minutes
exports.handler = async function(event, context) {
  if (event.httpMethod === 'GET') {
    try {
      await checkAvailability();
      return {
        statusCode: 200,
        body: JSON.stringify({ message: 'Slot check completed successfully' })
      };
    } catch (error) {
      return {
        statusCode: 500,
        body: JSON.stringify({ error: error.toString() })
      };
    }
  }
};
