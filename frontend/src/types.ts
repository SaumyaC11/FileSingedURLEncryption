export interface TrackedFile {
  fileId: string;
  filename: string;
  signedUrl?: string;
  expiresAt?: string;
  error?: string;
}
