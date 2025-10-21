// ABOUTME: Error message mapping for user-friendly error display
// ABOUTME: Converts technical errors to actionable user messages

interface ErrorMapping {
  pattern: RegExp | string;
  message: string;
  suggestion?: string;
}

const errorMappings: ErrorMapping[] = [
  {
    pattern: /file.*not.*csv/i,
    message: 'Invalid file type',
    suggestion: 'Please upload only CSV files'
  },
  {
    pattern: /file.*too.*large/i,
    message: 'File size exceeded',
    suggestion: 'Maximum file size is 10MB. Please split large files or compress them'
  },
  {
    pattern: /invalid.*csv.*format/i,
    message: 'CSV format error',
    suggestion: 'Please check that your file is a valid CSV with proper formatting'
  },
  {
    pattern: /duplicate.*transaction/i,
    message: 'Duplicate transactions detected',
    suggestion: 'These transactions may have already been imported. Review and confirm if you want to proceed'
  },
  {
    pattern: /missing.*required.*field/i,
    message: 'Incomplete data',
    suggestion: 'The CSV file is missing required columns. Please check the file format'
  },
  {
    pattern: /connection.*refused|network.*error|econnaborted/i,
    message: 'Connection error',
    suggestion: 'Unable to connect to the server. Please check your internet connection and try again'
  },
  {
    pattern: /unauthorized|401/i,
    message: 'Authentication failed',
    suggestion: 'Your session may have expired. Please refresh the page and try again'
  },
  {
    pattern: /server.*error|500|502|503/i,
    message: 'Server error',
    suggestion: 'The server is experiencing issues. Please try again in a few moments'
  },
  {
    pattern: /timeout/i,
    message: 'Request timed out',
    suggestion: 'The upload is taking too long. Try uploading fewer files at once'
  },
  {
    pattern: /unsupported.*file.*type/i,
    message: 'Unsupported file format',
    suggestion: 'This file type is not recognized. Supported formats: Revolut Metals, Revolut Stocks, Koinly Crypto'
  }
];

export function getErrorMessage(error: any): { title: string; message: string } {
  // Check if error has a response with data
  const errorString = error?.response?.data?.detail ||
                      error?.response?.data?.message ||
                      error?.message ||
                      String(error);

  // Try to match against known error patterns
  for (const mapping of errorMappings) {
    const pattern = typeof mapping.pattern === 'string'
      ? mapping.pattern
      : mapping.pattern;

    if (typeof pattern === 'string' && errorString.toLowerCase().includes(pattern.toLowerCase())) {
      return {
        title: mapping.message,
        message: mapping.suggestion || errorString
      };
    } else if (pattern instanceof RegExp && pattern.test(errorString)) {
      return {
        title: mapping.message,
        message: mapping.suggestion || errorString
      };
    }
  }

  // Default error message
  return {
    title: 'Upload failed',
    message: errorString.length > 100
      ? errorString.substring(0, 100) + '...'
      : errorString
  };
}

export function getFileTypeError(filename: string): string | null {
  if (!filename.toLowerCase().endsWith('.csv')) {
    return 'Only CSV files are supported';
  }

  const fileType = detectFileTypeFromName(filename);
  if (fileType === 'UNKNOWN') {
    return 'Unrecognized CSV format. Expected: Revolut Metals (account-statement_*), Revolut Stocks (UUID), or Koinly Crypto';
  }

  return null;
}

function detectFileTypeFromName(filename: string): string {
  if (filename.startsWith('account-statement_')) {
    return 'METALS';
  }

  const uuidPattern = /^[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}\.csv$/i;
  if (uuidPattern.test(filename)) {
    return 'STOCKS';
  }

  if (filename.toLowerCase().includes('koinly')) {
    return 'CRYPTO';
  }

  return 'UNKNOWN';
}