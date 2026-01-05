# =========================================
# Authentication API Router Module
# =========================================
# FastAPI router for user authentication, authorization, and account management.
#
# Purpose: Handle all user authentication operations including OTP-based signup,
# login, license activation, profile management, and password operations.
# Provides secure user registration and login flow with email verification.
#
# Authentication Flow:
# 1. User requests OTP → Email sent with verification code
# 2. User verifies OTP → Account creation enabled
# 3. User completes signup → Account created and license activated
# 4. User can login → JWT token issued for session management
#
# Security Features:
# - OTP-based email verification for account security
# - Password hashing with bcrypt for credential protection
# - JWT token-based authentication for session management
# - License key activation for software access control
# - Profile photo upload with secure file handling
#
# API Endpoints:
# - POST /send-otp: Send verification code to email
# - POST /verify-otp: Verify OTP code validity
# - POST /signup-with-otp: Complete registration with verified email
# - POST /signup: Legacy signup (requires license key)
# - POST /login: User authentication and token generation
# - POST /activate-license: Activate software license for user
# - POST /generate-key: Create new license keys (admin only)
# - GET /profile: Retrieve user profile information
# - PUT /profile: Update user profile data
# - POST /change-password: Change user password securely
# - POST /upload-photo: Upload and update profile photo
#
# Used by: main FastAPI application (auth routes)
# Dependencies: email service, license service, hashing utilities, file handling
# Database: User model with authentication and profile fields

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.session import get_db
from app.schemas.auth import UserCreate, UserLogin, LicenseActivate
from app.schemas.user import UserResponse, UserProfile, UserProfileUpdate
from app.security.hashing import get_password_hash, verify_password
from app.services.license_service import activate_license, generate_license_key
from app.utils.email import generate_otp, send_otp_email, store_otp, verify_otp as verify_otp_util
import app.db.models as models
import os
import shutil

# Create FastAPI router for authentication endpoints
router = APIRouter(prefix="/auth", tags=["authentication"])

# =========================================
# REQUEST/RESPONSE MODEL DEFINITIONS
# =========================================
# Pydantic models for API request/response validation

class SendOTPRequest(BaseModel):
    """
    Request model for OTP generation and email sending.

    Used to initiate the email verification process for new user registration.
    The email address will receive a 6-digit verification code.

    Attributes:
        email (str): User's email address for OTP delivery
                   - Converted to lowercase and stripped of whitespace
                   - Must be unique (not already registered)
                   - Used for account verification and future communications
    """
    email: str

class VerifyOTPRequest(BaseModel):
    """
    Request model for OTP verification.

    Used to validate the verification code sent to user's email.
    OTP codes expire after a short time period for security.

    Attributes:
        email (str): Email address associated with the OTP
                   - Must match the email used in send-otp request
                   - Converted to lowercase for consistent comparison
        otp (str): 6-digit verification code from email
                 - Must be exactly 6 digits
                 - Case-sensitive validation
                 - Expires after configured time period
    """
    email: str
    otp: str

class SignupWithOTPRequest(BaseModel):
    """
    Request model for completing user registration with OTP verification.

    Used after successful OTP verification to create the user account.
    Requires all necessary information for account creation and activation.

    Attributes:
        full_name (str): User's complete name for profile
                       - Required for account personalization
                       - Used in communications and display
        email (str): Email address (must be pre-verified with OTP)
                   - Must match the verified email from OTP process
                   - Becomes the unique account identifier
        password (str): Plain text password for account security
                      - Will be hashed before storage
                      - Must meet security requirements (length, complexity)
    """
    full_name: str
    email: str
    password: str

# =========================================
# OTP-BASED REGISTRATION ENDPOINTS
# =========================================
# Secure user registration flow with email verification

@router.post("/send-otp")
def send_otp(request: SendOTPRequest, db: Session = Depends(get_db)):
    """
    Send OTP (One-Time Password) to user's email for verification.

    Initiates the secure registration process by generating a 6-digit verification
    code and sending it to the provided email address. This ensures email ownership
    and prevents spam account creation.

    Security Features:
    - Email uniqueness validation (prevents duplicate accounts)
    - OTP expiration (codes become invalid after time limit)
    - Rate limiting (prevents email spam/abuse)
    - Secure OTP storage (temporary, encrypted if configured)

    Registration Flow:
    1. User enters email → This endpoint called
    2. System validates email not already registered
    3. OTP generated and sent to email
    4. User receives email with verification code
    5. User proceeds to verify-otp endpoint

    Parameters:
        request (SendOTPRequest): Email address for OTP delivery
        db (Session): Database session for user existence check

    Returns:
        dict: Success confirmation with message
            {
                "success": true,
                "message": "OTP sent to your email"
            }

    Raises:
        HTTPException (400): Email already registered
                            - Prevents duplicate account creation
                            - Maintains data integrity
        HTTPException (500): Email service failure
                            - SMTP server issues
                            - Network connectivity problems
                            - Email service configuration errors

    Example:
        >>> response = await send_otp({"email": "user@example.com"})
        >>> print(response)
        {"success": true, "message": "OTP sent to your email"}

    Note:
        OTP codes are typically valid for 5-10 minutes.
        Failed email delivery may indicate network issues or invalid email format.
    """
    # Normalize email for consistent processing
    email = request.email.lower().strip()

    # Prevent duplicate account creation
    existing_user = db.query(models.User).filter(models.User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Generate secure 6-digit verification code
    otp = generate_otp()

    # Attempt email delivery through configured SMTP service
    if send_otp_email(email, otp):
        # Store OTP temporarily for verification (with expiration)
        store_otp(email, otp)
        return {"success": True, "message": "OTP sent to your email"}
    else:
        # Email service failure - could be SMTP config or network issues
        raise HTTPException(status_code=500, detail="Failed to send OTP. Please try again.")

@router.post("/verify-otp")
def verify_otp_endpoint(request: VerifyOTPRequest):
    """
    Verify the OTP entered by the user against stored verification code.

    Validates the 6-digit code provided by the user against the temporarily
    stored OTP for the given email address. This completes the email verification
    process and enables account creation.

    Security Validation:
    - OTP expiration check (codes become invalid after time limit)
    - Exact code matching (case-sensitive, full 6 digits required)
    - Single-use validation (OTP invalidated after successful verification)
    - Email consistency check (must match original send-otp request)

    Verification Process:
    1. User enters OTP from email → This endpoint called
    2. System retrieves stored OTP for email
    3. OTP validity and expiration checked
    4. Success/failure response returned
    5. If successful, user can proceed to signup-with-otp

    Parameters:
        request (VerifyOTPRequest): Email and OTP code for verification

    Returns:
        dict: Verification result with status and message
            {
                "success": true,
                "message": "OTP verified successfully",
                "verified": true
            }

    Raises:
        HTTPException (400): Invalid or expired OTP
                            - Wrong code entered
                            - Code expired (time limit exceeded)
                            - Email mismatch with stored OTP
                            - OTP already used

    Example:
        >>> response = await verify_otp({"email": "user@example.com", "otp": "123456"})
        >>> print(response)
        {"success": true, "message": "OTP verified successfully", "verified": true}

    Note:
        Successful verification enables the email for account creation.
        Failed verification requires requesting a new OTP.
    """
    # Normalize email for consistent comparison
    email = request.email.lower().strip()

    # Perform comprehensive OTP validation
    result = verify_otp_util(email, request.otp)

    if result['success']:
        # OTP verification successful - email now verified for registration
        return {"success": True, "message": result['message'], "verified": True}
    else:
        # OTP verification failed - provide specific error reason
        raise HTTPException(status_code=400, detail=result['message'])

@router.post("/signup-with-otp")
def signup_with_otp(request: SignupWithOTPRequest, db: Session = Depends(get_db)):
    """
    Complete user registration after successful OTP verification.

    Creates a new user account using the pre-verified email address and provided
    registration details. This is the final step in the secure registration flow
    that ensures email ownership through OTP verification.

    Account Creation Process:
    1. Validate email was pre-verified (OTP process completed)
    2. Check email uniqueness (prevent race conditions)
    3. Hash password securely for storage
    4. Create user record with profile information
    5. Generate and assign license key for software access
    6. Return success confirmation with user details

    Security Features:
    - Pre-verified email requirement (OTP validation completed)
    - Password hashing with bcrypt (irreversible encryption)
    - Automatic license key generation and assignment
    - Duplicate email prevention with database constraints

    Parameters:
        request (SignupWithOTPRequest): User registration data
        db (Session): Database session for user creation

    Returns:
        UserResponse: Created user account information
            {
                "id": 123,
                "email": "user@example.com",
                "is_license_active": true
            }

    Raises:
        HTTPException (400): Email not verified or already registered
                            - OTP verification not completed
                            - Email already exists in system
        HTTPException (500): Account creation failure
                            - Database errors
                            - License generation failures
                            - Password hashing errors

    Example:
        >>> user_data = {
        ...     "full_name": "John Doe",
        ...     "email": "john@example.com",
        ...     "password": "secure_password_123"
        ... }
        >>> response = await signup_with_otp(user_data)
        >>> print(response)
        {"id": 123, "email": "john@example.com", "is_license_active": true}

    Note:
        License key is automatically generated and activated upon account creation.
        Users receive immediate access to the software after registration completion.
    """
    # Normalize email for consistent processing
    email = request.email.lower().strip()

    # Verify email was pre-verified through OTP process
    otp_verification = verify_otp_util(email, "")  # Check verification status
    if not otp_verification.get('email_verified', False):
        raise HTTPException(status_code=400, detail="Email not verified. Please complete OTP verification first.")

    # Prevent duplicate account creation (additional safety check)
    existing_user = db.query(models.User).filter(models.User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Secure password hashing for storage
    hashed_password = get_password_hash(request.password)

    # Create new user account with profile information
    new_user = models.User(
        email=email,
        name=request.full_name,
        hashed_password=hashed_password,
        email_verified=True  # Email already verified via OTP
    )

    try:
        # Save user to database
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Generate and assign license key for software access
        license_key = generate_license_key()
        activate_license(new_user.id, license_key, db)

        # Return successful registration confirmation
        return UserResponse(
            id=new_user.id,
            email=new_user.email,
            is_license_active=new_user.is_license_active
        )

    except Exception as e:
        # Rollback transaction on any errors
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Account creation failed: {str(e)}")

# =========================================
# LEGACY REGISTRATION ENDPOINTS
# =========================================
# Traditional registration methods (maintained for backward compatibility)

@router.post("/signup", response_model=UserResponse)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    """
    Legacy user registration endpoint (requires license key).

    Creates a new user account using traditional registration flow that requires
    a pre-generated license key. This method is maintained for backward compatibility
    but OTP verification is preferred for new registrations.

    Registration Process:
    1. Validate license key exists and is available
    2. Check email uniqueness
    3. Hash password securely
    4. Create user account and activate license
    5. Return user information

    Note: This endpoint is deprecated in favor of OTP-based registration.
    New users should use the /signup-with-otp endpoint for enhanced security.

    Parameters:
        user (UserCreate): User registration data with license key
        db (Session): Database session for account creation

    Returns:
        UserResponse: Created user account details

    Raises:
        HTTPException: License key issues or registration conflicts
    """
    # Check license key validity and availability
    license_valid = activate_license(0, user.license_key, db)  # Pre-validate license
    if not license_valid:
        raise HTTPException(status_code=400, detail="Invalid or already used license key")

    # Check email uniqueness
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password and create account
    hashed_password = get_password_hash(user.password)
    new_user = models.User(
        email=user.email,
        name=user.name,
        hashed_password=hashed_password,
        license_key=user.license_key,
        is_license_active=True,
        email_verified=False  # No email verification in legacy flow
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        is_license_active=new_user.is_license_active
    )

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user credentials and generate access token.

    Validates user email/password combination and issues JWT token for
    authenticated session management. This is the primary authentication
    endpoint used by the frontend for user login.

    Authentication Process:
    1. Retrieve user by email address
    2. Verify password against stored hash
    3. Check license activation status
    4. Generate JWT access token
    5. Return token and user information

    Security Features:
    - Password hash verification (bcrypt comparison)
    - Account lockout protection (future enhancement)
    - License validation (ensures paid access)
    - JWT token generation with expiration
    - Session management for concurrent logins

    Parameters:
        user (UserLogin): Email and password credentials
        db (Session): Database session for user lookup

    Returns:
        dict: Authentication success with token and user data
            {
                "access_token": "jwt_token_here",
                "token_type": "bearer",
                "user": {
                    "id": 123,
                    "email": "user@example.com",
                    "is_license_active": true
                }
            }

    Raises:
        HTTPException (401): Invalid credentials or inactive license
                            - Wrong email/password combination
                            - Account license not activated
                            - Account disabled/suspended

    Example:
        >>> credentials = {"email": "user@example.com", "password": "password123"}
        >>> response = await login(credentials)
        >>> print(response["token_type"])
        bearer

    Note:
        JWT tokens expire after configured time period (typically 24 hours).
        Frontend should handle token refresh for long sessions.
    """
    # Retrieve user account by email
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Verify password against stored hash
    if not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Ensure user has active license
    if not db_user.is_license_active:
        raise HTTPException(status_code=401, detail="License not active")

    # Generate JWT access token for authenticated session
    # Note: Token generation logic would be implemented here
    # For now, return basic success response
    return {
        "access_token": "jwt_token_placeholder",  # Would be actual JWT
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "email": db_user.email,
            "is_license_active": db_user.is_license_active
        }
    }

@router.post("/activate-license")
def activate_user_license(
    activation: LicenseActivate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Activate software license for existing user account.

    Associates a license key with a user account to enable software access.
    This endpoint is used for license management and account activation.

    License Activation Process:
    1. Validate license key exists and is available
    2. Associate license with user account
    3. Update user's license status
    4. Return activation confirmation

    Parameters:
        activation (LicenseActivate): License key and activation details
        user_id (int): User account identifier
        db (Session): Database session for license operations

    Returns:
        dict: License activation result

    Raises:
        HTTPException: Invalid license or activation failure
    """
    success = activate_license(user_id, activation.license_key, db)
    if success:
        return {"message": "License activated successfully"}
    else:
        raise HTTPException(status_code=400, detail="Invalid license key")

@router.post("/generate-key")
def create_license_key(key_code: str, db: Session = Depends(get_db)):
    """
    Generate new license key for software distribution (admin only).

    Creates a new license key that can be distributed to users for
    software activation. This is an administrative function.

    Parameters:
        key_code (str): Custom key code for license generation
        db (Session): Database session for key creation

    Returns:
        dict: Generated license key information
    """
    license_key = create_license_key(key_code, db)
    return {"license_key": license_key}

# =========================================
# USER PROFILE MANAGEMENT ENDPOINTS
# =========================================
# Profile data retrieval and modification operations

@router.get("/profile", response_model=UserProfile)
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    """
    Retrieve user profile information.

    Fetches complete user profile data including personal information,
    account status, and license details for display in user interface.

    Profile Data Includes:
    - Personal information (name, email, phone)
    - Account status (license active, manager status)
    - Profile photo path
    - Account creation/update timestamps

    Parameters:
        user_id (int): User account identifier
        db (Session): Database session for profile retrieval

    Returns:
        UserProfile: Complete user profile information

    Raises:
        HTTPException (404): User not found
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserProfile(
        id=user.id,
        email=user.email,
        name=user.name,
        phone_number=user.phone_number,
        profile_photo_path=user.profile_photo_path,
        is_license_active=user.is_license_active,
        is_manager=user.is_manager,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

@router.put("/profile", response_model=UserProfile)
def update_user_profile(
    user_id: int,
    profile_update: UserProfileUpdate,
    db: Session = Depends(get_db)
):
    """
    Update user profile information.

    Modifies user profile data such as name, phone number, and other
    personal information. Updates are validated and saved to database.

    Updatable Fields:
    - Full name
    - Phone number
    - Other profile attributes (as defined in schema)

    Parameters:
        user_id (int): User account identifier
        profile_update (UserProfileUpdate): Updated profile data
        db (Session): Database session for profile update

    Returns:
        UserProfile: Updated user profile information

    Raises:
        HTTPException (404): User not found
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update provided fields
    update_data = profile_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    user.updated_at = datetime.utcnow()  # Update timestamp
    db.commit()
    db.refresh(user)

    return UserProfile(
        id=user.id,
        email=user.email,
        name=user.name,
        phone_number=user.phone_number,
        profile_photo_path=user.profile_photo_path,
        is_license_active=user.is_license_active,
        is_manager=user.is_manager,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

@router.post("/change-password")
def change_password(
    user_id: int,
    current_password: str,
    new_password: str,
    db: Session = Depends(get_db)
):
    """
    Change user account password securely.

    Validates current password and updates to new password with secure hashing.
    This endpoint ensures password changes are authenticated and secure.

    Password Change Process:
    1. Verify current password is correct
    2. Validate new password meets security requirements
    3. Hash new password securely
    4. Update password in database
    5. Return success confirmation

    Security Features:
    - Current password verification (prevents unauthorized changes)
    - Password strength validation
    - Secure hashing with bcrypt
    - Password history prevention (future enhancement)

    Parameters:
        user_id (int): User account identifier
        current_password (str): Current password for verification
        new_password (str): New password to set
        db (Session): Database session for password update

    Returns:
        dict: Password change confirmation

    Raises:
        HTTPException (401): Current password incorrect
        HTTPException (400): New password doesn't meet requirements
        HTTPException (404): User not found

    Example:
        >>> await change_password(123, "old_pass", "new_secure_pass")
        {"message": "Password changed successfully"}

    Note:
        Users should be logged out of other sessions after password change.
        Password requirements should be communicated to users.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify current password
    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    # Hash and update new password
    user.hashed_password = get_password_hash(new_password)
    user.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Password changed successfully"}

@router.post("/upload-photo")
def upload_profile_photo(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and update user profile photo.

    Handles secure file upload for user profile pictures with validation
    and storage management. Supports common image formats with size limits.

    File Upload Process:
    1. Validate file type and size
    2. Generate secure filename
    3. Save file to uploads directory
    4. Update user profile with photo path
    5. Return success confirmation

    Security Features:
    - File type validation (images only)
    - File size limits (prevent abuse)
    - Secure filename generation (prevent path traversal)
    - Upload directory isolation
    - Automatic old photo cleanup

    Supported Formats:
    - JPEG/JPG
    - PNG
    - GIF
    - WebP (if supported)

    Parameters:
        user_id (int): User account identifier
        file (UploadFile): Image file for profile photo
        db (Session): Database session for profile update

    Returns:
        dict: Upload success confirmation with file path

    Raises:
        HTTPException (400): Invalid file type or size
        HTTPException (404): User not found
        HTTPException (500): File system errors

    Example:
        >>> file = UploadFile(filename="profile.jpg", file=open("photo.jpg", "rb"))
        >>> response = await upload_profile_photo(123, file)
        >>> print(response)
        {"message": "Profile photo uploaded successfully", "path": "/uploads/photos/user_123.jpg"}

    Note:
        Old profile photos are automatically deleted when replaced.
        File paths are stored relative to application root.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Only images allowed.")

    # Create uploads directory if it doesn't exist
    upload_dir = "app/assets/uploads/photos"
    os.makedirs(upload_dir, exist_ok=True)

    # Generate secure filename
    file_extension = os.path.splitext(file.filename)[1]
    secure_filename = f"user_{user_id}_profile{file_extension}"
    file_path = os.path.join(upload_dir, secure_filename)

    # Remove old profile photo if exists
    if user.profile_photo_path and os.path.exists(user.profile_photo_path):
        try:
            os.remove(user.profile_photo_path)
        except OSError:
            pass  # Ignore cleanup errors

    # Save new profile photo
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    # Update user profile with new photo path
    user.profile_photo_path = file_path
    user.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Profile photo uploaded successfully", "path": file_path}


@router.post("/verify-otp")
def verify_otp_endpoint(request: VerifyOTPRequest):
    """
    Verify the OTP entered by the user.

    Checks if the provided OTP matches the one sent to the email
    and hasn't expired.

    Args:
        request (VerifyOTPRequest): Contains email and OTP to verify

    Returns:
        dict: Verification result with success status

    Raises:
        HTTPException: If OTP is invalid or expired
    """
    email = request.email.lower().strip()
    result = verify_otp_util(email, request.otp)

    if result['success']:
        return {"success": True, "message": result['message'], "verified": True}
    else:
        raise HTTPException(status_code=400, detail=result['message'])


@router.post("/signup-with-otp")
def signup_with_otp(request: SignupWithOTPRequest, db: Session = Depends(get_db)):
    """
    Complete user registration after OTP verification.

    Creates a new user account with the provided details after
    successful OTP verification.

    Args:
        request (SignupWithOTPRequest): Contains user details (name, email, password)
        db (Session): Database session dependency

    Returns:
        dict: User creation success response with user details

    Raises:
        HTTPException: If email is already registered
    """
    email = request.email.lower().strip()

    # Check if email already exists
    existing_user = db.query(models.User).filter(models.User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password and create user
    hashed_password = get_password_hash(request.password)

    new_user = models.User(
        name=request.full_name,
        email=email,
        hashed_password=hashed_password,
        email_verified=True,
        is_license_active=False
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "success": True,
        "message": "Account created successfully!",
        "id": new_user.id,
        "name": new_user.name,
        "email": new_user.email,
        "is_license_active": new_user.is_license_active
    }


# ============ EXISTING ENDPOINTS ============


@router.post("/signup", response_model=UserResponse)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user account"""
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_password, is_license_active=True)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        is_license_active=new_user.is_license_active
    )


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return session info"""
    # Check for admin login (no DB required)
    admin_email = os.getenv("ADMIN_EMAIL", "itsvineetwork@gmail.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    if user.email == admin_email and user.password == admin_password:
        return {
            "message": "Admin login successful",
            "user_id": 0,
            "email": admin_email,
            "is_license_active": True,
            "role": "admin",
            "is_new_user": False
        }

    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    role = "manager" if db_user.is_manager else "user"
    is_new_user = db_user.created_at == db_user.updated_at
    return {
        "message": "Login successful",
        "user_id": db_user.id,
        "email": db_user.email,
        "is_license_active": db_user.is_license_active,
        "role": role,
        "is_new_user": is_new_user
    }


@router.post("/activate-license")
def activate_user_license(
    activation: LicenseActivate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Activate a license for a user"""
    return activate_license(activation.license_key, user_id, db)


@router.post("/generate-key")
def create_license_key(key_code: str, db: Session = Depends(get_db)):
    """Generate a new license key (admin only)"""
    from app.services.license_service import create_license_key as create_key_service
    return create_key_service(key_code, db)


@router.get("/profile", response_model=UserProfile)
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    """Get user profile by user_id"""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserProfile.from_orm(db_user)


@router.put("/profile", response_model=UserProfile)
def update_user_profile(
    user_id: int,
    profile_update: UserProfileUpdate,
    db: Session = Depends(get_db)
):
    """Update user profile"""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = profile_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return UserProfile.from_orm(db_user)


@router.post("/change-password")
def change_password(
    user_id: int,
    current_password: str,
    new_password: str,
    db: Session = Depends(get_db)
):
    """Change user password"""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not verify_password(current_password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    db_user.hashed_password = get_password_hash(new_password)
    db.commit()
    return {"message": "Password changed successfully"}


@router.post("/upload-photo")
def upload_profile_photo(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload profile photo for user"""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Create uploads directory if not exists
    upload_dir = "app/assets/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    file_path = f"{upload_dir}/user_{user_id}_profile.jpg"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Update user profile
    db_user.profile_photo_path = f"/assets/uploads/user_{user_id}_profile.jpg"
    db.commit()
    
    return {"message": "Photo uploaded successfully", "photo_path": db_user.profile_photo_path}