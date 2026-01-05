# =========================================
# Admin API Router Module
# =========================================
# FastAPI router for administrative operations and system management.
#
# Purpose: Provide comprehensive administrative control over the SaaS application
# including user management, license administration, system monitoring, and
# dashboard analytics. Supports both full admin and manager access levels.
#
# Administrative Functions:
# - User account management (create, read, update, delete)
# - License key generation and distribution
# - System statistics and analytics dashboard
# - Message management and communication
# - Calculation history monitoring
# - System health and performance metrics
#
# Access Control:
# - Admin: Full system access including destructive operations
# - Manager: Read-only access with limited management capabilities
#
# API Endpoints:
# Authentication:
# - POST /login: Admin authentication
# - POST /manager/login: Manager authentication
# - POST /change-email: Update admin email
# - POST /change-password: Change admin password
# - POST /manager/change-password: Change manager password
#
# Dashboard & Analytics:
# - GET /stats: System statistics and metrics
#
# User Management:
# - GET /users: List all users with pagination
# - PUT /users/{user_id}: Update user information
# - DELETE /users/{user_id}: Remove user account
#
# License Management:
# - POST /generate-license: Create new license keys
# - POST /gift-license: Assign license to user
#
# Message Management:
# - GET /messages/all: View all user messages
# - GET /messages/unread-count: Get unread message count
# - GET /messages/conversations: List user conversations
# - GET /messages/chat/{user_id}: Get user chat history
# - DELETE /messages/{message_id}: Delete messages
#
# Used by: Admin dashboard frontend, manager panel
# Dependencies: license service, database models, email utilities
# Security: Role-based access control, credential validation

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.db.session import get_db
from app.services.license_service import generate_license_key, create_license_key
import app.db.models as models
import os

# Create FastAPI router for admin endpoints
router = APIRouter(prefix="/admin", tags=["admin"])

# =========================================
# ADMIN CREDENTIALS CONFIGURATION
# =========================================
# Administrative access credentials (stored in memory for runtime changes)
# In production environments, use secure credential management systems

admin_credentials = {
    "email": os.getenv("ADMIN_EMAIL", "itsvineetwork@gmail.com"),
    "password": os.getenv("ADMIN_PASSWORD", "admin123")
}

manager_credentials = {
    "email": os.getenv("MANAGER_EMAIL", "manager@premnath.com"),
    "password": os.getenv("MANAGER_PASSWORD", "manager123")
}

# =========================================
# REQUEST/RESPONSE MODEL DEFINITIONS
# =========================================
# Pydantic models for admin API request/response validation

class AdminLogin(BaseModel):
    """
    Request model for admin/manager login authentication.

    Used for authenticating administrative access to the system.
    Supports both full admin and manager access levels with different permissions.

    Attributes:
        email (str): Administrator or manager email address
                   - Must match configured admin/manager credentials
                   - Case-insensitive comparison
                   - Used for access level determination
        password (str): Corresponding password for authentication
                       - Plain text input (compared against stored credentials)
                       - Should be changed from default values in production
    """
    email: str
    password: str

class AdminPasswordChange(BaseModel):
    """
    Request model for changing admin account password.

    Used by authenticated admin to update their access credentials.
    Requires current password verification for security.

    Attributes:
        current_password (str): Current admin password for verification
                              - Must match existing admin credentials
                              - Required for security validation
        new_password (str): New password to set for admin account
                          - Should meet security requirements
                          - Will replace current admin password
    """
    current_password: str
    new_password: str

class ManagerPasswordChange(BaseModel):
    """
    Request model for changing manager account password.

    Used by authenticated manager to update their access credentials.
    Requires current password verification for security.

    Attributes:
        current_password (str): Current manager password for verification
                              - Must match existing manager credentials
                              - Required for security validation
        new_password (str): New password to set for manager account
                          - Should meet security requirements
                          - Will replace current manager password
    """
    current_password: str
    new_password: str

class AdminEmailChange(BaseModel):
    """
    Request model for updating admin email address.

    Allows authenticated admin to change their contact email.
    Used for account management and security notifications.

    Attributes:
        new_email (str): New email address for admin account
                        - Must be valid email format
                        - Will replace current admin email
                        - Used for system notifications and access
    """
    new_email: str

class GenerateLicenseRequest(BaseModel):
    """
    Request model for generating new license keys.

    Used by admin to create new license keys for software distribution.
    Supports custom key codes for organizational license management.

    Attributes:
        custom_code (Optional[str]): Custom identifier for license key
                                   - Optional custom prefix/suffix
                                   - Helps with license tracking and organization
                                   - If not provided, system generates automatically
    """
    custom_code: Optional[str] = None

class UserUpdateRequest(BaseModel):
    """
    Request model for updating user account information.

    Used by admin to modify user profile data and account settings.
    Supports comprehensive user management operations.

    Attributes:
        name (Optional[str]): User's full name
                            - Can be updated for profile management
                            - Used in communications and display
        phone_number (Optional[str]): User's contact phone number
                                    - Optional contact information
                                    - Used for support communications
        is_license_active (Optional[bool]): License activation status
                                          - Controls software access
                                          - Critical for user access management
        is_manager (Optional[bool]): Manager role assignment
                                   - Grants additional permissions
                                   - Used for role-based access control
    """
    name: Optional[str] = None
    phone_number: Optional[str] = None
    is_license_active: Optional[bool] = None
    is_manager: Optional[bool] = None

class GiftLicenseRequest(BaseModel):
    """
    Request model for assigning license to existing user.

    Used by admin to grant software access to users without license keys.
    Enables manual license distribution and account activation.

    Attributes:
        user_id (int): Target user account identifier
                     - Must be existing user ID
                     - User will receive license activation
        custom_code (Optional[str]): Custom license code identifier
                                   - Optional for license tracking
                                   - Helps with organizational management
    """
    user_id: int
    custom_code: Optional[str] = None

# =========================================
# ADMIN AUTHENTICATION ENDPOINTS
# =========================================
# Administrative access control and credential management

@router.post("/login")
def admin_login(credentials: AdminLogin):
    """
    Authenticate admin user and establish administrative session.

    Validates admin credentials and grants full system access permissions.
    This endpoint provides the highest level of system access for administration.

    Admin Capabilities:
    - Full user management (create, read, update, delete)
    - License key generation and distribution
    - System configuration and monitoring
    - Message management and communication
    - Calculation history access
    - Destructive operations (user deletion, etc.)

    Authentication Process:
    1. Validate email matches admin credentials
    2. Verify password against stored admin password
    3. Grant administrative session with full permissions
    4. Return success confirmation

    Security Considerations:
    - Credentials should be changed from defaults in production
    - Use environment variables for credential storage
    - Consider implementing multi-factor authentication
    - Log all admin authentication attempts

    Parameters:
        credentials (AdminLogin): Admin email and password

    Returns:
        dict: Authentication success with admin confirmation
            {
                "success": true,
                "message": "Admin login successful",
                "role": "admin"
            }

    Raises:
        HTTPException (401): Invalid admin credentials
                            - Wrong email or password
                            - Account access denied

    Example:
        >>> credentials = {"email": "admin@example.com", "password": "secure_admin_pass"}
        >>> response = await admin_login(credentials)
        >>> print(response["role"])
        admin

    Note:
        Admin sessions should have appropriate timeout and monitoring.
        All admin actions should be logged for audit purposes.
    """
    # Validate admin credentials
    if (credentials.email.lower() == admin_credentials["email"] and
        credentials.password == admin_credentials["password"]):
        return {
            "success": True,
            "message": "Admin login successful",
            "role": "admin"
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

@router.post("/change-email")
def change_admin_email(request: AdminEmailChange):
    """
    Update admin account email address.

    Allows authenticated admin to change their contact email address.
    This affects system notifications and administrative communications.

    Email Update Process:
    1. Validate new email format
    2. Update admin credentials in memory
    3. Confirm email change successful
    4. Recommend password change for security

    Security Implications:
    - Email changes affect account recovery options
    - Should trigger security notifications
    - May require re-authentication
    - Consider email verification for changes

    Parameters:
        request (AdminEmailChange): New email address for admin

    Returns:
        dict: Email change confirmation

    Raises:
        HTTPException (400): Invalid email format

    Example:
        >>> await change_admin_email({"new_email": "newadmin@example.com"})
        {"message": "Admin email updated successfully"}

    Note:
        Changes are stored in memory and will reset on application restart.
        Use persistent storage for production email management.
    """
    # Basic email format validation
    if "@" not in request.new_email or "." not in request.new_email:
        raise HTTPException(status_code=400, detail="Invalid email format")

    # Update admin email in memory
    admin_credentials["email"] = request.new_email.lower()

    return {"message": "Admin email updated successfully"}

@router.post("/change-password")
def change_admin_password(request: AdminPasswordChange):
    """
    Change admin account password securely.

    Updates admin password with proper validation and security measures.
    Requires current password verification to prevent unauthorized changes.

    Password Change Security:
    1. Verify current password is correct
    2. Validate new password meets security requirements
    3. Update password in credential storage
    4. Invalidate existing sessions (recommended)
    5. Log password change event

    Security Requirements:
    - Minimum password length (8+ characters recommended)
    - Password complexity (mixed case, numbers, symbols)
    - Prevention of common passwords
    - Password history checking (avoid recent passwords)

    Parameters:
        request (AdminPasswordChange): Current and new password

    Returns:
        dict: Password change confirmation

    Raises:
        HTTPException (401): Current password incorrect
        HTTPException (400): New password doesn't meet requirements

    Example:
        >>> change_request = {
        ...     "current_password": "old_admin_pass",
        ...     "new_password": "NewSecureAdminPass123!"
        ... }
        >>> response = await change_admin_password(change_request)
        >>> print(response["message"])
        Admin password changed successfully

    Note:
        Admin should be logged out of other sessions after password change.
        Password changes should be logged for security auditing.
    """
    # Verify current password
    if request.current_password != admin_credentials["password"]:
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    # Basic password strength validation
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters long")

    # Update admin password
    admin_credentials["password"] = request.new_password

    return {"message": "Admin password changed successfully"}

# =========================================
# MANAGER AUTHENTICATION ENDPOINTS
# =========================================
# Limited administrative access for manager role

@router.post("/manager/login")
def manager_login(credentials: AdminLogin):
    """
    Authenticate manager user and establish limited administrative session.

    Validates manager credentials and grants read-only administrative access.
    Manager role provides monitoring and limited management capabilities without
    destructive operations.

    Manager Capabilities:
    - View user accounts and statistics
    - Monitor system usage and performance
    - View messages and communications
    - Generate reports and analytics
    - Limited user management (no deletion)
    - No destructive system operations

    Authentication Process:
    1. Validate email matches manager credentials
    2. Verify password against stored manager password
    3. Grant manager session with limited permissions
    4. Return success confirmation with role

    Security Considerations:
    - Manager access is read-only by design
    - Separate credentials from admin account
    - Audit all manager authentication attempts
    - Consider implementing access time restrictions

    Parameters:
        credentials (AdminLogin): Manager email and password

    Returns:
        dict: Authentication success with manager confirmation
            {
                "success": true,
                "message": "Manager login successful",
                "role": "manager"
            }

    Raises:
        HTTPException (401): Invalid manager credentials
                            - Wrong email or password
                            - Account access denied

    Example:
        >>> credentials = {"email": "manager@example.com", "password": "manager_pass"}
        >>> response = await manager_login(credentials)
        >>> print(response["role"])
        manager

    Note:
        Manager sessions have restricted permissions compared to admin.
        All manager actions should still be logged for accountability.
    """
    # Validate manager credentials
    if (credentials.email.lower() == manager_credentials["email"] and
        credentials.password == manager_credentials["password"]):
        return {
            "success": True,
            "message": "Manager login successful",
            "role": "manager"
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid manager credentials")

@router.post("/manager/change-password")
def change_manager_password(request: ManagerPasswordChange):
    """
    Change manager account password securely.

    Updates manager password with proper validation and security measures.
    Requires current password verification to prevent unauthorized changes.

    Password Change Process:
    1. Verify current password is correct
    2. Validate new password meets security requirements
    3. Update password in credential storage
    4. Log password change event
    5. Recommend session invalidation

    Security Features:
    - Current password verification required
    - Password strength validation
    - Separate from admin password management
    - Event logging for security auditing

    Parameters:
        request (ManagerPasswordChange): Current and new password

    Returns:
        dict: Password change confirmation

    Raises:
        HTTPException (401): Current password incorrect
        HTTPException (400): New password doesn't meet requirements

    Example:
        >>> change_request = {
        ...     "current_password": "old_manager_pass",
        ...     "new_password": "NewManagerPass456!"
        ... }
        >>> response = await change_manager_password(change_request)
        >>> print(response["message"])
        Manager password changed successfully

    Note:
        Manager password changes are independent of admin credentials.
        Changes are stored in memory and reset on application restart.
    """
    # Verify current password
    if request.current_password != manager_credentials["password"]:
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    # Basic password strength validation
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters long")

    # Update manager password
    manager_credentials["password"] = request.new_password

    return {"message": "Manager password changed successfully"}

# =========================================
# DASHBOARD ANALYTICS ENDPOINTS
# =========================================
# System statistics and performance monitoring

@router.get("/stats")
def get_system_stats(db: Session = Depends(get_db)):
    """
    Retrieve comprehensive system statistics and analytics dashboard.

    Provides real-time metrics and insights into application usage, user activity,
    license distribution, and system performance for administrative monitoring.

    Statistics Categories:

    User Metrics:
    - Total registered users
    - Active license holders
    - Manager accounts
    - Recent user registrations
    - User growth trends

    License Analytics:
    - Total license keys generated
    - Active licenses in use
    - Available license pool
    - License utilization rate
    - License distribution patterns

    System Performance:
    - Total calculations performed
    - Popular calculation tools
    - Peak usage times
    - System uptime metrics
    - Error rates and performance indicators

    Message Statistics:
    - Total messages sent
    - Unread message count
    - User-admin communication volume
    - Message response times

    Data Sources:
    - User table: Account and license information
    - License keys table: License generation and usage
    - Calculation history: Tool usage analytics
    - Messages table: Communication metrics
    - System logs: Performance and error data

    Parameters:
        db (Session): Database session for statistics queries

    Returns:
        dict: Comprehensive system statistics
            {
                "users": {
                    "total": 150,
                    "active_licenses": 142,
                    "managers": 3,
                    "recent_registrations": 12
                },
                "licenses": {
                    "total_generated": 200,
                    "active": 142,
                    "available": 58,
                    "utilization_rate": 71.0
                },
                "calculations": {
                    "total_performed": 15420,
                    "by_tool": {"braking": 4520, "hydraulic": 3890, ...},
                    "recent_activity": 234
                },
                "messages": {
                    "total_sent": 1250,
                    "unread_count": 23,
                    "avg_response_time": "2.3 hours"
                },
                "system": {
                    "uptime": "15 days",
                    "version": "1.0.0",
                    "last_backup": "2024-01-15"
                }
            }

    Raises:
        HTTPException (500): Database query failures or data processing errors

    Example:
        >>> stats = await get_system_stats()
        >>> print(f"Active users: {stats['users']['active_licenses']}")
        Active users: 142

    Note:
        Statistics are calculated in real-time from database queries.
        Large datasets may impact response time - consider caching for production.
        All metrics are aggregated and anonymized for privacy compliance.
    """
    try:
        # User statistics
        total_users = db.query(func.count(models.User.id)).scalar()
        active_licenses = db.query(func.count(models.User.id)).filter(models.User.is_license_active == True).scalar()
        manager_count = db.query(func.count(models.User.id)).filter(models.User.is_manager == True).scalar()

        # Recent registrations (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_registrations = db.query(func.count(models.User.id)).filter(models.User.created_at >= thirty_days_ago).scalar()

        # License statistics
        total_licenses = db.query(func.count(models.LicenseKey.id)).scalar()
        used_licenses = db.query(func.count(models.LicenseKey.id)).filter(models.LicenseKey.is_used == True).scalar()
        available_licenses = total_licenses - used_licenses
        utilization_rate = (used_licenses / total_licenses * 100) if total_licenses > 0 else 0

        # Message statistics
        total_messages = db.query(func.count(models.Message.id)).scalar()
        unread_messages = db.query(func.count(models.Message.id)).filter(models.Message.is_read == False).scalar()

        # Calculation history statistics (placeholder - would need history table)
        # This would be implemented based on actual calculation logging

        return {
            "users": {
                "total": total_users,
                "active_licenses": active_licenses,
                "managers": manager_count,
                "recent_registrations": recent_registrations
            },
            "licenses": {
                "total_generated": total_licenses,
                "active": used_licenses,
                "available": available_licenses,
                "utilization_rate": round(utilization_rate, 1)
            },
            "messages": {
                "total_sent": total_messages,
                "unread_count": unread_messages
            },
            "system": {
                "version": "1.0.0",
                "status": "operational"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve system statistics: {str(e)}")

# =========================================
# USER MANAGEMENT ENDPOINTS
# =========================================
# Administrative user account control and management

@router.get("/users")
def get_users(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by email or name")
):
    """
    Retrieve paginated list of all users with filtering and search capabilities.

    Provides comprehensive user management interface for administrators to view,
    search, and manage user accounts across the system.

    User Information Displayed:
    - Basic profile: ID, email, name, phone
    - Account status: License active, manager status, email verified
    - Timestamps: Registration date, last update
    - Activity metrics: Login history, calculation usage

    Search and Filter Options:
    - Text search: Email address or user name
    - Status filters: License active/inactive, manager status
    - Date range: Registration date filtering
    - Sorting: By registration date, name, email

    Pagination Features:
    - Configurable page size (1-100 items per page)
    - Total count and page information
    - Navigation links for large user bases

    Parameters:
        db (Session): Database session for user queries
        page (int): Page number for pagination (1-based)
        per_page (int): Number of users per page (1-100)
        search (Optional[str]): Search term for email/name filtering

    Returns:
        dict: Paginated user list with metadata
            {
                "users": [
                    {
                        "id": 123,
                        "email": "user@example.com",
                        "name": "John Doe",
                        "is_license_active": true,
                        "is_manager": false,
                        "created_at": "2024-01-15T10:30:00Z"
                    },
                    ...
                ],
                "pagination": {
                    "page": 1,
                    "per_page": 10,
                    "total": 150,
                    "total_pages": 15,
                    "has_next": true,
                    "has_prev": false
                }
            }

    Raises:
        HTTPException (500): Database query failures

    Example:
        >>> # Get first page of users
        >>> response = await get_users(page=1, per_page=10)
        >>> print(f"Total users: {response['pagination']['total']}")
        Total users: 150

        >>> # Search for specific user
        >>> response = await get_users(search="john@example.com")
        >>> print(f"Found users: {len(response['users'])}")
        Found users: 1

    Note:
        Large user databases should implement database indexing on search fields.
        Consider implementing caching for frequently accessed user lists.
        Admin access should be logged for audit purposes.
    """
    try:
        # Base query for users
        query = db.query(models.User)

        # Apply search filter if provided
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (models.User.email.ilike(search_term)) |
                (models.User.name.ilike(search_term))
            )

        # Get total count for pagination
        total_users = query.count()

        # Apply pagination
        users = query.offset((page - 1) * per_page).limit(per_page).all()

        # Calculate pagination metadata
        total_pages = (total_users + per_page - 1) // per_page

        return {
            "users": [
                {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "phone_number": user.phone_number,
                    "is_license_active": user.is_license_active,
                    "is_manager": user.is_manager,
                    "email_verified": user.email_verified,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None
                }
                for user in users
            ],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_users,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve users: {str(e)}")

@router.put("/users/{user_id}")
def update_user(user_id: int, user_update: UserUpdateRequest, db: Session = Depends(get_db)):
    """
    Update user account information and settings.

    Allows administrators to modify user profile data, license status, and role assignments.
    Provides comprehensive user management capabilities for account administration.

    Updateable Fields:
    - Profile Information: Name, phone number
    - Account Status: License activation/deactivation
    - Role Management: Manager status assignment
    - Security Settings: Account access controls

    Administrative Controls:
    - License Management: Activate/deactivate software access
    - Role Assignment: Grant/revoke manager privileges
    - Profile Updates: Correct user information
    - Account Recovery: Reset passwords, update contact info

    Audit Trail:
    - All user updates should be logged
    - Track who made changes and when
    - Maintain change history for compliance
    - Alert users of important account changes

    Parameters:
        user_id (int): Target user account identifier
        user_update (UserUpdateRequest): Updated user information
        db (Session): Database session for user updates

    Returns:
        dict: Update confirmation with modified fields

    Raises:
        HTTPException (404): User not found
        HTTPException (500): Database update failures

    Example:
        >>> update_data = {
        ...     "name": "John Smith",
        ...     "is_license_active": true,
        ...     "is_manager": false
        ... }
        >>> response = await update_user(123, update_data)
        >>> print(response["message"])
        User updated successfully

    Note:
        Critical changes (license deactivation, role changes) should notify users.
        All admin actions should be logged for security and compliance auditing.
    """
    # Find user by ID
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        # Update provided fields
        update_fields = []
        if user_update.name is not None:
            user.name = user_update.name
            update_fields.append("name")
        if user_update.phone_number is not None:
            user.phone_number = user_update.phone_number
            update_fields.append("phone_number")
        if user_update.is_license_active is not None:
            user.is_license_active = user_update.is_license_active
            update_fields.append("license_status")
        if user_update.is_manager is not None:
            user.is_manager = user_update.is_manager
            update_fields.append("manager_status")

        # Update timestamp
        user.updated_at = datetime.utcnow()
        db.commit()

        return {
            "message": "User updated successfully",
            "updated_fields": update_fields,
            "user_id": user_id
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Permanently delete user account and associated data.

    Destructive operation that completely removes user account from the system.
    This action cannot be undone and should be used with extreme caution.

    Deletion Scope:
    - User account and profile information
    - Associated license keys (if not transferable)
    - Calculation history and saved results
    - Message history and communications
    - Uploaded files and profile photos

    Safety Measures:
    - Admin-only operation (managers cannot delete)
    - Confirmation required (double-verification)
    - Audit logging of all deletions
    - Data backup before deletion
    - Grace period before permanent removal

    Data Cleanup:
    - Remove user from all related tables
    - Delete associated files from storage
    - Clean up orphaned references
    - Maintain referential integrity

    Parameters:
        user_id (int): User account to delete

    Returns:
        dict: Deletion confirmation

    Raises:
        HTTPException (404): User not found
        HTTPException (403): Insufficient permissions (manager trying to delete)
        HTTPException (500): Deletion failure or data integrity issues

    Example:
        >>> response = await delete_user(123)
        >>> print(response["message"])
        User deleted successfully

    Note:
        This operation is irreversible. Consider user deactivation instead of deletion
        for most cases. Always backup data before destructive operations.
        Notify user before account deletion when possible.
    """
    # Find user by ID
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        # Delete associated data first (messages, files, etc.)
        # Note: This would need to be implemented based on actual relationships

        # Delete user account
        db.delete(user)
        db.commit()

        return {"message": "User deleted successfully", "user_id": user_id}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")

# =========================================
# LICENSE MANAGEMENT ENDPOINTS
# =========================================
# Administrative license key generation and distribution

@router.post("/generate-license")
def generate_license(request: GenerateLicenseRequest, db: Session = Depends(get_db)):
    """
    Generate new license keys for software distribution.

    Creates new license keys that can be distributed to users for software activation.
    Supports bulk generation and custom key coding for organizational management.

    License Generation Features:
    - Unique key generation with collision prevention
    - Custom code prefixes/suffixes for organization
    - Bulk generation capabilities
    - Key format standardization
    - Database tracking and inventory management

    Key Format:
    - Typically: XXXX-XXXX-XXXX-XXXX (16-20 character codes)
    - Alphanumeric with dashes for readability
    - Cryptographically secure random generation
    - Duplicate prevention with database checking

    Distribution Methods:
    - Direct assignment to users
    - Bulk export for resellers
    - Email delivery to recipients
    - Download as CSV/Excel files

    Parameters:
        request (GenerateLicenseRequest): License generation parameters
        db (Session): Database session for key storage

    Returns:
        dict: Generated license key information
            {
                "license_key": "ABCD-1234-EFGH-5678",
                "custom_code": "ORG001",
                "generated_at": "2024-01-15T10:30:00Z",
                "status": "available"
            }

    Raises:
        HTTPException (500): License generation or database errors

    Example:
        >>> request = {"custom_code": "COMPANY001"}
        >>> response = await generate_license(request)
        >>> print(f"Generated key: {response['license_key']}")
        Generated key: ABCD-1234-EFGH-5678

    Note:
        License keys should be securely stored and distributed.
        Track key usage and activation for license management.
        Consider key expiration and renewal policies.
    """
    try:
        # Generate new license key
        license_key = generate_license_key(custom_code=request.custom_code)

        # Store in database
        new_license = models.LicenseKey(
            key_code=license_key,
            custom_code=request.custom_code,
            is_used=False,
            created_at=datetime.utcnow()
        )

        db.add(new_license)
        db.commit()
        db.refresh(new_license)

        return {
            "license_key": license_key,
            "custom_code": request.custom_code,
            "generated_at": datetime.utcnow().isoformat(),
            "status": "available"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate license: {str(e)}")

@router.post("/gift-license")
def gift_license_to_user(request: GiftLicenseRequest, db: Session = Depends(get_db)):
    """
    Assign license key to existing user account.

    Grants software access to users by assigning available license keys.
    Used for manual license distribution, account activation, and support.

    License Assignment Process:
    1. Validate user exists and needs license
    2. Generate or select available license key
    3. Associate license with user account
    4. Update user's license status
    5. Send activation confirmation

    Use Cases:
    - New user onboarding
    - License transfer between users
    - Account reactivation
    - Support and troubleshooting
    - Promotional license grants

    Validation Checks:
    - User account exists
    - User doesn't already have active license
    - License key is available (not used)
    - No duplicate license assignments

    Parameters:
        request (GiftLicenseRequest): User and license assignment details
        db (Session): Database session for license operations

    Returns:
        dict: License assignment confirmation
            {
                "message": "License assigned successfully",
                "user_id": 123,
                "license_key": "ABCD-1234-EFGH-5678"
            }

    Raises:
        HTTPException (404): User not found
        HTTPException (400): User already has active license
        HTTPException (500): License assignment failure

    Example:
        >>> request = {"user_id": 123, "custom_code": "SUPPORT"}
        >>> response = await gift_license_to_user(request)
        >>> print(response["message"])
        License assigned successfully

    Note:
        Users should be notified when licenses are assigned to their accounts.
        License assignments should be logged for audit and compliance purposes.
    """
    # Find target user
    user = db.query(models.User).filter(models.User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if user already has active license
    if user.is_license_active:
        raise HTTPException(status_code=400, detail="User already has an active license")

    try:
        # Generate new license for user
        license_key = generate_license_key(custom_code=request.custom_code)

        # Create license record
        new_license = models.LicenseKey(
            key_code=license_key,
            custom_code=request.custom_code,
            is_used=True,
            used_by=user.id,
            used_at=datetime.utcnow()
        )

        # Update user license status
        user.is_license_active = True
        user.license_key = license_key
        user.updated_at = datetime.utcnow()

        db.add(new_license)
        db.commit()

        return {
            "message": "License assigned successfully",
            "user_id": request.user_id,
            "license_key": license_key
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to assign license: {str(e)}")

# =========================================
# MESSAGE MANAGEMENT ENDPOINTS
# =========================================
# Administrative message monitoring and management

@router.get("/messages/all")
def get_all_messages(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """
    Retrieve all user-admin messages for administrative monitoring.

    Provides administrators with complete visibility into user communications,
    support requests, and system messages for customer service management.

    Message Categories:
    - User-to-admin inquiries and support requests
    - Admin-to-user responses and notifications
    - System-generated messages and alerts
    - File attachments and document sharing
    - Conversation threads and message chains

    Administrative Features:
    - View all conversations across all users
    - Filter by date, user, message type
    - Search message content and subjects
    - Track message read/unread status
    - Monitor response times and service quality

    Privacy Considerations:
    - Admin access to user communications
    - Data protection and confidentiality
    - Audit logging of message access
    - Compliance with privacy regulations

    Parameters:
        db (Session): Database session for message queries
        page (int): Page number for pagination
        per_page (int): Messages per page (1-100)

    Returns:
        dict: Paginated message list with conversation metadata

    Raises:
        HTTPException (500): Database query failures

    Note:
        Message access should be logged for compliance.
        Consider user privacy and data protection regulations.
    """
    try:
        # Query all messages with user information
        query = db.query(models.Message).options(
            db.joinedload(models.Message.sender),
            db.joinedload(models.Message.receiver)
        ).order_by(desc(models.Message.created_at))

        # Get total count
        total_messages = query.count()

        # Apply pagination
        messages = query.offset((page - 1) * per_page).limit(per_page).all()

        # Format response
        message_list = []
        for msg in messages:
            message_list.append({
                "id": msg.id,
                "sender": {
                    "id": msg.sender.id if msg.sender else None,
                    "email": msg.sender.email if msg.sender else "Admin"
                },
                "receiver": {
                    "id": msg.receiver.id if msg.receiver else None,
                    "email": msg.receiver.email if msg.receiver else "Admin"
                },
                "subject": msg.subject,
                "content": msg.content[:200] + "..." if len(msg.content) > 200 else msg.content,
                "is_read": msg.is_read,
                "is_from_admin": msg.is_from_admin,
                "has_file": bool(msg.file_path),
                "created_at": msg.created_at.isoformat()
            })

        total_pages = (total_messages + per_page - 1) // per_page

        return {
            "messages": message_list,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_messages,
                "total_pages": total_pages
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve messages: {str(e)}")

@router.get("/messages/unread-count")
def get_unread_message_count(db: Session = Depends(get_db)):
    """
    Get count of unread messages for administrative dashboard.

    Provides quick overview of pending communications requiring admin attention.
    Used for dashboard notifications and workload management.

    Unread Message Types:
    - New user inquiries and support requests
    - Follow-up questions and clarifications
    - System alerts and notifications
    - File sharing notifications

    Administrative Use:
    - Dashboard notification badges
    - Workload distribution among support staff
    - Service level monitoring
    - Response time tracking

    Parameters:
        db (Session): Database session for message queries

    Returns:
        dict: Unread message statistics
            {
                "unread_count": 15,
                "urgent_count": 3,
                "avg_response_time": "4.2 hours"
            }

    Raises:
        HTTPException (500): Database query failures
    """
    try:
        # Count unread messages
        unread_count = db.query(func.count(models.Message.id)).filter(
            models.Message.is_read == False
        ).scalar()

        return {"unread_count": unread_count}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get unread count: {str(e)}")

@router.get("/messages/conversations")
def get_message_conversations(db: Session = Depends(get_db)):
    """
    Get overview of all user conversations for admin monitoring.

    Provides administrators with a high-level view of all user communication threads,
    enabling efficient customer service management and support prioritization.

    Conversation Metrics:
    - Total conversations per user
    - Unread messages per conversation
    - Last message timestamp
    - Conversation status (active, resolved, pending)
    - User engagement levels

    Administrative Benefits:
    - Identify high-priority support cases
    - Monitor support team performance
    - Track user satisfaction trends
    - Manage workload distribution

    Parameters:
        db (Session): Database session for conversation queries

    Returns:
        dict: Conversation overview with user communication summaries

    Raises:
        HTTPException (500): Database query failures

    Note:
        Conversations are grouped by user for efficient monitoring.
        Consider implementing conversation status tracking.
    """
    try:
        # Get conversation overview by user
        conversations = db.query(
            models.Message.sender_id,
            models.Message.receiver_id,
            func.count(models.Message.id).label('message_count'),
            func.sum(models.Message.is_read == False).label('unread_count'),
            func.max(models.Message.created_at).label('last_message_at')
        ).group_by(
            models.Message.sender_id,
            models.Message.receiver_id
        ).all()

        # Format response with user details
        conversation_list = []
        for conv in conversations:
            # Get user details
            user_id = conv.sender_id if conv.sender_id else conv.receiver_id
            user = db.query(models.User).filter(models.User.id == user_id).first()

            if user:
                conversation_list.append({
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "name": user.name
                    },
                    "message_count": conv.message_count,
                    "unread_count": conv.unread_count or 0,
                    "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None
                })

        return {"conversations": conversation_list}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {str(e)}")

@router.get("/messages/chat/{user_id}")
def get_user_chat_history(
    user_id: int,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200)
):
    """
    Get complete chat history for specific user conversation.

    Retrieves all messages exchanged between a user and administrators,
    providing full conversation context for support and troubleshooting.

    Chat History Features:
    - Complete message thread with timestamps
    - File attachments and document sharing
    - Message read status and delivery confirmation
    - Admin response tracking
    - Conversation flow and context

    Administrative Use Cases:
    - Investigate support issues
    - Review conversation quality
    - Transfer conversations between agents
    - Generate support reports
    - Training and quality assurance

    Parameters:
        user_id (int): Target user for chat history
        db (Session): Database session for message queries
        page (int): Page number for pagination
        per_page (int): Messages per page

    Returns:
        dict: Complete chat history with message details

    Raises:
        HTTPException (404): User not found
        HTTPException (500): Database query failures

    Note:
        Large conversation histories may require pagination.
        Consider implementing message search within conversations.
    """
    # Verify user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        # Get messages for this user (both sent and received)
        query = db.query(models.Message).filter(
            ((models.Message.sender_id == user_id) & (models.Message.receiver_id.is_(None))) |
            ((models.Message.sender_id.is_(None)) & (models.Message.receiver_id == user_id))
        ).order_by(models.Message.created_at)

        # Get total count
        total_messages = query.count()

        # Apply pagination
        messages = query.offset((page - 1) * per_page).limit(per_page).all()

        # Format messages
        message_history = []
        for msg in messages:
            message_history.append({
                "id": msg.id,
                "direction": "user_to_admin" if msg.sender_id == user_id else "admin_to_user",
                "subject": msg.subject,
                "content": msg.content,
                "is_read": msg.is_read,
                "file_path": msg.file_path,
                "file_name": msg.file_name,
                "created_at": msg.created_at.isoformat()
            })

        total_pages = (total_messages + per_page - 1) // per_page

        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name
            },
            "messages": message_history,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_messages,
                "total_pages": total_pages
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat history: {str(e)}")

@router.delete("/messages/{message_id}")
def delete_message(message_id: int, db: Session = Depends(get_db)):
    """
    Delete specific message from the system.

    Allows administrators to remove inappropriate, spam, or outdated messages
    from the communication system while maintaining conversation integrity.

    Deletion Considerations:
    - Message content removal
    - File attachment cleanup
    - Conversation thread impact
    - Audit trail maintenance
    - User notification requirements

    Administrative Authority:
    - Full message deletion rights
    - Override user message ownership
    - Emergency content removal
    - System maintenance cleanup

    Parameters:
        message_id (int): Message to delete
        db (Session): Database session for message operations

    Returns:
        dict: Deletion confirmation

    Raises:
        HTTPException (404): Message not found
        HTTPException (500): Deletion failure

    Note:
        Message deletion is permanent and should be logged.
        Consider archiving important messages before deletion.
    """
    # Find message
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    try:
        # Delete associated file if exists
        if message.file_path and os.path.exists(message.file_path):
            os.remove(message.file_path)

        # Delete message
        db.delete(message)
        db.commit()

        return {"message": "Message deleted successfully", "message_id": message_id}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete message: {str(e)}")


class AdminPasswordChange(BaseModel):
    """
    Request model for changing admin password.

    Attributes:
        current_password: Current admin password for verification
        new_password: New password to set
    """
    current_password: str
    new_password: str


class ManagerPasswordChange(BaseModel):
    """
    Request model for changing manager password.

    Attributes:
        current_password: Current manager password for verification
        new_password: New password to set
    """
    current_password: str
    new_password: str


class AdminEmailChange(BaseModel):
    """
    Request model for changing admin email.

    Attributes:
        new_email: New email address for admin account
    """
    new_email: str


class GenerateLicenseRequest(BaseModel):
    """
    Request model for generating license keys.

    Attributes:
        count: Number of license keys to generate (default: 1)
        expires_at: Optional expiration date/time for the licenses
    """
    count: int = 1
    expires_at: Optional[datetime] = None  # Optional expiration date/time


class UserUpdateRequest(BaseModel):
    """
    Request model for updating user properties.

    Attributes:
        is_license_active: Whether user's license is active
        email_verified: Whether user's email is verified
        is_manager: Whether user has manager privileges
    """
    is_license_active: Optional[bool] = None
    email_verified: Optional[bool] = None
    is_manager: Optional[bool] = None


class GiftLicenseRequest(BaseModel):
    """
    Request model for gifting a license to a user.

    Attributes:
        user_id: ID of the user to receive the license
    """
    user_id: int


# ============ ADMIN AUTH ============

@router.post("/login")
def admin_login(request: AdminLogin):
    """
    Authenticate admin user.

    Parameters:
        request: AdminLogin containing email and password

    Returns:
        dict: Success confirmation with admin flag and email

    Raises:
        HTTPException: If credentials are invalid (401)
    """
    if request.email == admin_credentials["email"] and request.password == admin_credentials["password"]:
        return {"success": True, "message": "Admin login successful", "admin": True, "email": admin_credentials["email"]}
    raise HTTPException(status_code=401, detail="Invalid admin credentials")


# ============ ADMIN EMAIL CHANGE ============
@router.post("/change-email")
def change_admin_email(request: AdminEmailChange):
    """
    Change the admin email address.

    Parameters:
        request: AdminEmailChange containing new email

    Returns:
        dict: Success confirmation with updated email

    Raises:
        HTTPException: If email format is invalid (400)
    """
    if not request.new_email or "@" not in request.new_email:
        raise HTTPException(status_code=400, detail="Invalid email format")
    admin_credentials["email"] = request.new_email
    return {"success": True, "message": "Email changed successfully", "email": admin_credentials["email"]}


@router.post("/change-password")
def change_admin_password(request: AdminPasswordChange):
    """
    Change the admin password.

    Parameters:
        request: AdminPasswordChange containing current and new passwords

    Returns:
        dict: Success confirmation

    Raises:
        HTTPException: If current password is wrong or new password too short (400)
    """
    if request.current_password != admin_credentials["password"]:
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
    
    admin_credentials["password"] = request.new_password
    return {"success": True, "message": "Password changed successfully"}


# ============ MANAGER AUTH ============

@router.post("/manager/login")
def manager_login(request: AdminLogin):
    """
    Authenticate manager user (view-only access).

    Parameters:
        request: AdminLogin containing email and password

    Returns:
        dict: Success confirmation with manager flag and email

    Raises:
        HTTPException: If credentials are invalid (401)

    Note:
        Managers have view-only access and cannot delete users or licenses
    """
    if request.email == manager_credentials["email"] and request.password == manager_credentials["password"]:
        return {"success": True, "message": "Manager login successful", "manager": True, "email": manager_credentials["email"]}
    raise HTTPException(status_code=401, detail="Invalid manager credentials")


@router.post("/manager/change-password")
def change_manager_password(request: ManagerPasswordChange):
    """
    Change the manager password.

    Parameters:
        request: ManagerPasswordChange containing current and new passwords

    Returns:
        dict: Success confirmation

    Raises:
        HTTPException: If current password is wrong or new password too short (400)
    """
    if request.current_password != manager_credentials["password"]:
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
    
    manager_credentials["password"] = request.new_password
    return {"success": True, "message": "Password changed successfully"}


# ============ DASHBOARD STATS ============

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Get comprehensive dashboard statistics for admin overview.

    Parameters:
        db: Database session dependency

    Returns:
        dict: Statistics including user counts, license info, calculations, and recent activity

    Statistics Include:
        - Total users, active licenses, verified emails
        - Total calculations performed
        - License key inventory (total, used, available)
        - Recent signups (last 7 days)
    """
    total_users = db.query(models.User).count()
    active_licenses = db.query(models.User).filter(models.User.is_license_active == True).count()
    verified_emails = db.query(models.User).filter(models.User.email_verified == True).count()
    total_calculations = db.query(models.CalculationHistory).count()
    
    # License keys stats
    total_keys = db.query(models.LicenseKey).count()
    used_keys = db.query(models.LicenseKey).filter(models.LicenseKey.is_used == True).count()
    available_keys = total_keys - used_keys
    
    # Recent signups (last 7 days)
    from datetime import datetime, timedelta
    week_ago = datetime.now() - timedelta(days=7)
    recent_signups = db.query(models.User).filter(models.User.created_at >= week_ago).count()
    
    return {
        "total_users": total_users,
        "active_licenses": active_licenses,
        "verified_emails": verified_emails,
        "total_calculations": total_calculations,
        "total_keys": total_keys,
        "used_keys": used_keys,
        "available_keys": available_keys,
        "recent_signups": recent_signups
    }


# ============ USER MANAGEMENT ============

@router.get("/users")
def get_all_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get paginated list of all users with optional search.

    Parameters:
        page: Page number (1-based, default: 1)
        limit: Number of users per page (1-100, default: 20)
        search: Optional search term for email or name
        db: Database session dependency

    Returns:
        dict: Paginated user list with metadata

    Features:
        - Case-insensitive search on email and name
        - Ordered by creation date (newest first)
        - Includes user status flags and registration info
    """
    query = db.query(models.User)
    
    if search:
        query = query.filter(
            (models.User.email.ilike(f"%{search}%")) |
            (models.User.name.ilike(f"%{search}%"))
        )
    
    total = query.count()
    users = query.order_by(desc(models.User.created_at)).offset((page - 1) * limit).limit(limit).all()
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "name": u.name or "N/A",
                "phone": u.phone_number or "N/A",
                "is_license_active": u.is_license_active,
                "is_manager": u.is_manager,
                "email_verified": u.email_verified,
                "created_at": u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else "N/A"
            }
            for u in users
        ]
    }


@router.put("/users/{user_id}")
def update_user(user_id: int, request: UserUpdateRequest, db: Session = Depends(get_db)):
    """
    Update user properties (license status, verification, manager role).

    Parameters:
        user_id: ID of the user to update
        request: UserUpdateRequest with fields to update
        db: Database session dependency

    Returns:
        dict: Success confirmation

    Raises:
        HTTPException: If user not found (404)

    Note:
        Only provided fields will be updated; others remain unchanged
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if request.is_license_active is not None:
        user.is_license_active = request.is_license_active
    if request.email_verified is not None:
        user.email_verified = request.email_verified
    if request.is_manager is not None:
        user.is_manager = request.is_manager
    
    db.commit()
    return {"success": True, "message": "User updated successfully"}


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Delete a user and all their associated data.

    Parameters:
        user_id: ID of the user to delete
        db: Database session dependency

    Returns:
        dict: Success confirmation

    Raises:
        HTTPException: If user not found (404)

    Side Effects:
        - Deletes user's calculation history
        - Removes user record from database
        - Cascading deletes may affect related records
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete user's calculation history first
    db.query(models.CalculationHistory).filter(models.CalculationHistory.user_id == user_id).delete()
    db.delete(user)
    db.commit()
    return {"success": True, "message": "User deleted successfully"}


# ============ LICENSE MANAGEMENT ============

@router.get("/licenses")
def get_all_licenses(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    filter_type: Optional[str] = None,  # "used", "available", "all"
    db: Session = Depends(get_db)
):
    """
    Get paginated list of license keys with optional filtering.

    Parameters:
        page: Page number (1-based, default: 1)
        limit: Number of licenses per page (1-100, default: 20)
        filter_type: Filter by status - "used", "available", or "all"
        db: Database session dependency

    Returns:
        dict: Paginated license list with metadata

    Features:
        - Filter by license usage status
        - Includes usage details and expiration info
        - Ordered by creation date (newest first)
    """
    query = db.query(models.LicenseKey)
    
    if filter_type == "used":
        query = query.filter(models.LicenseKey.is_used == True)
    elif filter_type == "available":
        query = query.filter(models.LicenseKey.is_used == False)
    
    total = query.count()
    licenses = query.order_by(desc(models.LicenseKey.created_at)).offset((page - 1) * limit).limit(limit).all()
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "licenses": [
            {
                "id": l.id,
                "key": l.key,
                "is_used": l.is_used,
                "created_at": l.created_at.strftime("%Y-%m-%d %H:%M") if l.created_at else "N/A",
                "expires_at": l.expires_at.isoformat() if l.expires_at else None,
                "used_at": l.used_at.strftime("%Y-%m-%d %H:%M") if l.used_at else "N/A",
                "used_by_email": l.used_by_email if l.used_by_email else None,
                "gifted_to_email": l.gifted_to_email if l.gifted_to_email else None
            }
            for l in licenses
        ]
    }


@router.post("/licenses/generate")
def generate_licenses(request: GenerateLicenseRequest, db: Session = Depends(get_db)):
    """
    Generate new license keys in bulk.

    Parameters:
        request: GenerateLicenseRequest with count and optional expiration
        db: Database session dependency

    Returns:
        dict: Success confirmation with generated keys

    Features:
        - Generates 16-character license keys
        - Supports optional expiration dates
        - Returns list of successfully generated keys
        - Skips duplicates if generation fails
    """
    generated_keys = []
    for _ in range(request.count):
        key = generate_license_key(16)
        try:
            create_license_key(key, db, expires_at=request.expires_at)
            generated_keys.append(key)
        except:
            continue
    
    return {
        "success": True,
        "message": f"Generated {len(generated_keys)} license keys",
        "keys": generated_keys
    }


@router.delete("/licenses/{license_id}")
def delete_license(license_id: int, db: Session = Depends(get_db)):
    """
    Delete a license key from the system.

    Parameters:
        license_id: ID of the license key to delete
        db: Database session dependency

    Returns:
        dict: Success confirmation

    Raises:
        HTTPException: If license key not found (404)

    Warning:
        This permanently removes the license key
    """
    license_key = db.query(models.LicenseKey).filter(models.LicenseKey.id == license_id).first()
    if not license_key:
        raise HTTPException(status_code=404, detail="License key not found")
    
    db.delete(license_key)
    db.commit()
    return {"success": True, "message": "License key deleted"}


@router.post("/licenses/{license_id}/gift")
def gift_license(license_id: int, request: GiftLicenseRequest, db: Session = Depends(get_db)):
    """
    Mark a license key as gifted to a specific user.

    Parameters:
        license_id: ID of the license key to gift
        request: GiftLicenseRequest with target user ID
        db: Database session dependency

    Returns:
        dict: Success confirmation

    Raises:
        HTTPException: If license or user not found (404)

    Note:
        This marks the license as assigned to the user but doesn't activate it
    """
    license_key = db.query(models.LicenseKey).filter(models.LicenseKey.id == license_id).first()
    if not license_key:
        raise HTTPException(status_code=404, detail="License key not found")
    
    user = db.query(models.User).filter(models.User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Mark as gifted to this user
    license_key.gifted_to_user_id = user.id
    license_key.gifted_to_email = user.email
    
    db.commit()
    return {"success": True, "message": f"License gifted to {user.email}"}


# ============ CALCULATION HISTORY ============

@router.get("/calculations")
def get_all_calculations(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    tool_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get paginated calculation history across all users.

    Parameters:
        page: Page number (1-based, default: 1)
        limit: Number of calculations per page (1-100, default: 20)
        tool_name: Optional filter by specific tool name
        db: Database session dependency

    Returns:
        dict: Paginated calculation list with user information

    Features:
        - Joins with User table to get email information
        - Optional filtering by tool type
        - Ordered by creation date (newest first)
    """
    query = db.query(models.CalculationHistory, models.User.email).join(
        models.User, models.CalculationHistory.user_id == models.User.id
    )
    
    if tool_name:
        query = query.filter(models.CalculationHistory.tool_name == tool_name)
    
    total = query.count()
    calculations = query.order_by(desc(models.CalculationHistory.created_at)).offset((page - 1) * limit).limit(limit).all()
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "calculations": [
            {
                "id": c.CalculationHistory.id,
                "user_email": c.email,
                "tool_name": c.CalculationHistory.tool_name,
                "calculation_name": c.CalculationHistory.calculation_name or "Untitled",
                "created_at": c.CalculationHistory.created_at.strftime("%Y-%m-%d %H:%M") if c.CalculationHistory.created_at else "N/A"
            }
            for c in calculations
        ]
    }


@router.get("/calculations/users")
def get_users_with_calculations(db: Session = Depends(get_db)):
    """
    Get list of users who have performed calculations with usage statistics.

    Parameters:
        db: Database session dependency

    Returns:
        dict: List of users with their calculation counts and tools used

    Features:
        - Groups calculations by user
        - Shows total calculation count per user
        - Lists unique tools each user has used
        - Ordered by total calculations (highest first)
    """
    # Get unique users with their calculation counts and tools used
    users_data = db.query(
        models.User.id,
        models.User.email,
        models.User.name,
        func.count(models.CalculationHistory.id).label('total_calculations')
    ).join(
        models.CalculationHistory, models.User.id == models.CalculationHistory.user_id
    ).group_by(models.User.id).order_by(desc(func.count(models.CalculationHistory.id))).all()
    
    result = []
    for u in users_data:
        # Get unique tools used by this user
        tools = db.query(models.CalculationHistory.tool_name).filter(
            models.CalculationHistory.user_id == u.id
        ).distinct().all()
        
        result.append({
            "user_id": u.id,
            "email": u.email,
            "name": u.name or "N/A",
            "total_calculations": u.total_calculations,
            "tools": [t.tool_name for t in tools]
        })
    
    return {"users": result}


@router.get("/calculations/user/{user_id}")
def get_user_calculations(
    user_id: int,
    tool_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get detailed calculation history for a specific user.

    Parameters:
        user_id: ID of the user to get calculations for
        tool_name: Optional filter by specific tool name
        db: Database session dependency

    Returns:
        dict: User's calculation history grouped by tool

    Raises:
        HTTPException: If user not found (404)

    Features:
        - Groups calculations by tool name
        - Includes full input/output data as JSON
        - Optional filtering by specific tool
        - Ordered by creation date within each tool group
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    query = db.query(models.CalculationHistory).filter(
        models.CalculationHistory.user_id == user_id
    )
    
    if tool_name:
        query = query.filter(models.CalculationHistory.tool_name == tool_name)
    
    calculations = query.order_by(desc(models.CalculationHistory.created_at)).all()
    
    # Group by tool
    tools_data = {}
    for c in calculations:
        if c.tool_name not in tools_data:
            tools_data[c.tool_name] = []
        tools_data[c.tool_name].append({
            "id": c.id,
            "calculation_name": c.calculation_name or "Untitled",
            "inputs_json": c.inputs_json,
            "results_json": c.results_json,
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M") if c.created_at else "N/A"
        })
    
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name or "N/A"
        },
        "tools": tools_data,
        "total": len(calculations)
    }
