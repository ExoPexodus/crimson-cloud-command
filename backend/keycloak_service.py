from keycloak import KeycloakOpenID
from typing import Optional, Dict, Any, List
import os
import logging

logger = logging.getLogger(__name__)

class KeycloakService:
    def __init__(self):
        self.server_url = os.getenv("KEYCLOAK_SERVER_URL")
        self.realm = os.getenv("KEYCLOAK_REALM")
        self.client_id = os.getenv("KEYCLOAK_CLIENT_ID")
        self.client_secret = os.getenv("KEYCLOAK_CLIENT_SECRET")
        
        if not all([self.server_url, self.realm, self.client_id]):
            logger.warning("Keycloak configuration incomplete - Keycloak authentication disabled")
            self.keycloak_client = None
            return
            
        try:
            self.keycloak_client = KeycloakOpenID(
                server_url=self.server_url,
                client_id=self.client_id,
                realm_name=self.realm,
                client_secret_key=self.client_secret
            )
        except Exception as e:
            logger.error(f"Failed to initialize Keycloak client: {e}")
            self.keycloak_client = None
    
    def is_enabled(self) -> bool:
        """Check if Keycloak is properly configured and enabled"""
        return self.keycloak_client is not None
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate Keycloak token and return user info"""
        if not self.is_enabled():
            return None
            
        try:
            # Introspect token to validate it
            token_info = self.keycloak_client.introspect(token)
            
            if not token_info.get('active'):
                logger.warning("Keycloak token is not active")
                return None
                
            # Get detailed user info
            user_info = self.keycloak_client.userinfo(token)
            
            return {
                'token_info': token_info,
                'user_info': user_info
            }
            
        except Exception as e:
            logger.error(f"Keycloak token validation failed: {e}")
            return None
    
    def get_user_roles(self, token: str) -> List[str]:
        """Extract user roles from Keycloak token"""
        if not self.is_enabled():
            return []
            
        try:
            token_info = self.keycloak_client.introspect(token)
            
            if not token_info.get('active'):
                return []
            
            # Extract roles from different possible locations
            roles = []
            
            # Client-specific roles
            resource_access = token_info.get('resource_access', {})
            client_roles = resource_access.get(self.client_id, {}).get('roles', [])
            roles.extend(client_roles)
            
            # Realm roles
            realm_access = token_info.get('realm_access', {})
            realm_roles = realm_access.get('roles', [])
            roles.extend(realm_roles)
            
            # Also check for groups (Keycloak groups are often mapped as roles)
            groups = token_info.get('groups', [])
            if groups:
                roles.extend(groups)
            
            # Print to console for easy debugging
            print(f"\n=== KEYCLOAK ROLES EXTRACTION ===")
            print(f"Client roles: {client_roles}")
            print(f"Realm roles: {realm_roles}")
            print(f"Groups: {groups}")
            print(f"All combined roles/groups: {roles}")
            print(f"================================\n")
                
            logger.info(f"Keycloak roles and groups extracted: {roles}")
            
            return roles
            
        except Exception as e:
            logger.error(f"Failed to get user roles from Keycloak: {e}")
            return []
    
    def exchange_code_for_token(self, code: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token"""
        import base64
        import json
        
        if not self.is_enabled():
            logger.error("❌ Keycloak client not enabled - cannot exchange code")
            return None
            
        try:
            # Log all details for debugging
            logger.info("=" * 80)
            logger.info("🔄 KEYCLOAK CODE EXCHANGE ATTEMPT")
            logger.info("=" * 80)
            logger.info(f"📍 Server URL: {self.server_url}")
            logger.info(f"🏰 Realm: {self.realm}")
            logger.info(f"🔑 Client ID: {self.client_id}")
            logger.info(f"🔐 Client Secret: {'SET (length: ' + str(len(self.client_secret)) + ')' if self.client_secret else 'NOT SET'}")
            logger.info(f"📋 Authorization Code: {code[:20]}...{code[-10:] if len(code) > 30 else code}")
            logger.info(f"↩️  Redirect URI: {redirect_uri}")
            logger.info("=" * 80)
            
            # Attempt token exchange
            token = self.keycloak_client.token(
                grant_type='authorization_code',
                code=code,
                redirect_uri=redirect_uri
            )
            
            logger.info("✅ Successfully exchanged code for token")
            logger.info(f"🎫 Token type: {token.get('token_type', 'unknown')}")
            logger.info(f"⏰ Expires in: {token.get('expires_in', 'unknown')} seconds")
            
            # Decode and log JWT access token claims
            access_token = token.get('access_token')
            if access_token:
                try:
                    parts = access_token.split('.')
                    if len(parts) == 3:
                        # Add padding if needed
                        payload_b64 = parts[1]
                        padding = 4 - len(payload_b64) % 4
                        if padding != 4:
                            payload_b64 += '=' * padding
                        payload = base64.urlsafe_b64decode(payload_b64)
                        decoded_claims = json.loads(payload)
                        
                        print("\n" + "=" * 80)
                        print("🔍 DECODED JWT ACCESS TOKEN CLAIMS:")
                        print("=" * 80)
                        for key, value in decoded_claims.items():
                            print(f"  {key}: {value}")
                        print("=" * 80)
                        
                        # Specifically highlight group-related claims
                        print("\n🎭 GROUP-RELATED CLAIMS (IMPORTANT FOR ROLE MAPPING):")
                        print(f"  groups: {decoded_claims.get('groups', 'NOT PRESENT')}")
                        print(f"  realm_access.roles: {decoded_claims.get('realm_access', {}).get('roles', 'NOT PRESENT')}")
                        print(f"  resource_access: {decoded_claims.get('resource_access', 'NOT PRESENT')}")
                        
                        # Log to file as well
                        logger.info("=" * 80)
                        logger.info("🔍 DECODED JWT ACCESS TOKEN CLAIMS:")
                        logger.info("=" * 80)
                        for key, value in decoded_claims.items():
                            logger.info(f"  {key}: {value}")
                        logger.info("=" * 80)
                        logger.info("🎭 GROUP-RELATED CLAIMS:")
                        logger.info(f"  groups: {decoded_claims.get('groups', 'NOT PRESENT')}")
                        logger.info(f"  realm_access.roles: {decoded_claims.get('realm_access', {}).get('roles', 'NOT PRESENT')}")
                        logger.info(f"  resource_access: {decoded_claims.get('resource_access', 'NOT PRESENT')}")
                        
                        # Store decoded claims in token for later use
                        token['decoded_claims'] = decoded_claims
                except Exception as decode_error:
                    logger.warning(f"⚠️ Could not decode JWT for logging: {decode_error}")
                    print(f"⚠️ Could not decode JWT for logging: {decode_error}")
            
            return token
            
        except Exception as e:
            logger.error("=" * 80)
            logger.error("❌ KEYCLOAK CODE EXCHANGE FAILED")
            logger.error("=" * 80)
            logger.error(f"🔥 Error Type: {type(e).__name__}")
            logger.error(f"💬 Error Message: {str(e)}")
            
            # Try to extract more details from the exception
            if hasattr(e, 'response'):
                logger.error(f"📡 Response Status: {getattr(e.response, 'status_code', 'N/A')}")
                logger.error(f"📨 Response Body: {getattr(e.response, 'text', 'N/A')}")
            
            # Log full traceback
            import traceback
            logger.error(f"📚 Full Traceback:\n{traceback.format_exc()}")
            logger.error("=" * 80)
            
            return None

# Global instance
keycloak_service = KeycloakService()