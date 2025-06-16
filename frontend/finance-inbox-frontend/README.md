# Finance Inbox Frontend

React frontend for the Finance Inbox application built with Vite, Tailwind CSS, and modern React practices.

## 🏗️ Architecture

```
finance-inbox-frontend/
├── src/                  # Source code
│   ├── components/      # React components
│   ├── pages/          # Page components
│   ├── hooks/          # Custom React hooks
│   ├── utils/          # Utility functions
│   ├── assets/         # Static assets
│   ├── App.jsx         # Main App component
│   └── main.jsx        # Application entry point
├── public/             # Public assets
├── package.json        # Dependencies and scripts
├── vite.config.js      # Vite configuration
├── tailwind.config.js  # Tailwind CSS configuration
├── postcss.config.js   # PostCSS configuration
└── README.md           # This file
```

## 🛠️ Prerequisites

- **Node.js 16+**
- **npm** or **yarn** package manager

## 📦 Installation

### 1. Install Dependencies
```bash
npm install
```

### 2. Environment Configuration
Create a `.env` file in the frontend directory (if needed):
```bash
VITE_API_URL=http://localhost:8000
VITE_CLERK_PUBLISHABLE_KEY=your_clerk_key
```

## 🚀 Running the Application

### Development Mode
```bash
npm run dev
```

The application will be available at http://localhost:5173

### Build for Production
```bash
npm run build
```

### Preview Production Build
```bash
npm run preview
```

## 🧪 Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run lint:fix` - Fix ESLint issues

### Code Structure

- **Components**: Reusable UI components
- **Pages**: Page-level components
- **Hooks**: Custom React hooks for business logic
- **Utils**: Helper functions and utilities
- **Assets**: Images, icons, and other static files

### Styling

The application uses **Tailwind CSS** for styling:
- Utility-first CSS framework
- Responsive design
- Dark mode support (if implemented)
- Custom components and design system

### State Management

- React Context for global state
- Local state with useState and useReducer
- Custom hooks for complex state logic

## 🔧 Configuration

### Vite Configuration
The application uses Vite for fast development and building:
- Hot Module Replacement (HMR)
- Fast refresh for React
- Optimized production builds

### Tailwind Configuration
Custom Tailwind configuration in `tailwind.config.js`:
- Custom color palette
- Responsive breakpoints
- Component variants

### ESLint Configuration
Code quality and consistency:
- React-specific rules
- Import/export rules
- Code formatting

## 🔌 API Integration

The frontend communicates with the backend API:
- **Base URL**: http://localhost:8000 (configurable)
- **Authentication**: Clerk integration
- **Data Fetching**: Fetch API or Axios
- **Error Handling**: Centralized error handling

## 📱 Features

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Modern UI**: Clean, intuitive interface
- **Fast Performance**: Optimized with Vite
- **Type Safety**: JavaScript with ESLint for code quality
- **Accessibility**: WCAG compliant components

## 🧪 Testing

### Running Tests
```bash
npm test
```

### Test Structure
- Unit tests for components
- Integration tests for pages
- E2E tests for critical flows

## 🚀 Deployment

### Build for Production
```bash
npm run build
```

### Deployment Options
- **Vercel**: Automatic deployments from Git
- **Netlify**: Static site hosting
- **AWS S3**: Static website hosting
- **Docker**: Containerized deployment

## 🔒 Security

- Environment variables for sensitive data
- Input validation and sanitization
- XSS protection
- CORS configuration

## 📊 Performance

- Code splitting and lazy loading
- Optimized bundle size
- Image optimization
- Caching strategies

## 🆘 Troubleshooting

### Common Issues

#### Port Conflicts
If port 5173 is in use:
```bash
npm run dev -- --port 3000
```

#### Build Issues
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### ESLint Issues
```bash
# Fix automatically
npm run lint:fix
```

### Development Tips

1. **Use React DevTools** for debugging
2. **Check the console** for errors and warnings
3. **Use the Network tab** to debug API calls
4. **Enable source maps** for better debugging

## 📝 Contributing

1. Follow the existing code style
2. Write meaningful commit messages
3. Test your changes thoroughly
4. Update documentation as needed
5. Create descriptive pull requests

## 📞 Support

For frontend-specific issues:
1. Check the troubleshooting section above
2. Review the browser console for errors
3. Check the Network tab for API issues
4. Create an issue in the repository

## 🔗 Related Links

- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)
- [Backend API Documentation](http://localhost:8000/docs)
