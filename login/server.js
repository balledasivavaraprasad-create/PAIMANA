require('dotenv').config();
const express = require('express');
const cookieParser = require('cookie-parser');
const path = require('path');
const authRoutes = require('./authRoutes');

const app = express();
app.use(express.json());
app.use(cookieParser());

// Serves your existing HTML page (place Project_2.html in a "public" folder,
// or point this at wherever the file actually lives).
app.use(express.static(path.join(__dirname, 'public')));

app.use('/api', authRoutes);

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on http://localhost:${PORT}`));
