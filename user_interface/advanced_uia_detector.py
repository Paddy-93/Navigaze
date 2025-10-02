#!/usr/bin/env python3
"""
Advanced UIA-based text field detection using comtypes for deep web app support.
Based on ChatGPT's recommendations for Electron/WebView apps like Spotify.
Enhanced with scrollable element detection and boundary management.
"""

import sys

try:
    import comtypes.client
    try:
        from comtypes.gen.UIAutomationClient import (
            IUIAutomation, TreeScope_Subtree, TreeScope_Element,
            UIA_ControlTypePropertyId, UIA_IsEnabledPropertyId,
            UIA_IsPasswordAttributeId, UIA_IsReadOnlyAttributeId,
            UIA_EditControlTypeId, UIA_DocumentControlTypeId, UIA_ComboBoxControlTypeId
        )
    except ImportError:
        # If the generated comtypes interfaces aren't available, use raw values
        IUIAutomation = None
        TreeScope_Subtree = 7
        TreeScope_Element = 2
        UIA_ControlTypePropertyId = 30003
        UIA_IsEnabledPropertyId = 30010
        UIA_IsPasswordAttributeId = 40025
        UIA_IsReadOnlyAttributeId = 40015
        UIA_EditControlTypeId = 50004
        UIA_DocumentControlTypeId = 50030
        UIA_ComboBoxControlTypeId = 50003
    COMTYPES_AVAILABLE = True
except ImportError:
    COMTYPES_AVAILABLE = False

class AdvancedUIA:
    """Advanced UIA detector that can penetrate web app content and handle scrollable elements."""
    
    def __init__(self, debug=False):
        self._uia = None
        self._last_result = False
        self.debug = debug  # Enable debug output for troubleshooting
        self._com_initialized = False
        
    def _get_uia(self):
        """Get or create UIA automation object with proper COM initialization."""
        if not COMTYPES_AVAILABLE:
            return None
        try:
            if self._uia is None:
                # Initialize COM first
                import comtypes
                try:
                    comtypes.CoInitialize()
                    self._com_initialized = True
                except OSError:
                    # Already initialized, that's fine
                    pass
                
                # Use ChatGPT's recommended approach: load UIAutomationCore.dll first
                import comtypes.client as cc
                
                # Generate/load wrappers directly from the DLL
                cc.GetModule('UIAutomationCore.dll')
                
                # Import generated interfaces & coclasses
                from comtypes.gen.UIAutomationClient import IUIAutomation, CUIAutomation
                
                # Create the object using the coclass and request the interface
                self._uia = cc.CreateObject(CUIAutomation, interface=IUIAutomation)
                print("UIA Debug: Successfully created with COM initialization")
                
            return self._uia
        except Exception as e:
            print(f"UIA Debug: Failed to create UIA object: {e}")
            # Try fallback approach
            try:
                import comtypes
                comtypes.CoInitialize()
                import comtypes.client
                self._uia = comtypes.client.CreateObject("UIAutomation.CUIAutomation")
                print("UIA Debug: Successfully created using fallback approach")
                return self._uia
            except Exception as e2:
                print(f"UIA Debug: Fallback also failed: {e2}")
                return None

    def _supports_pattern(self, element, pattern_id):
        """Check if element supports a specific UIA pattern."""
        try:
            pattern = element.GetCurrentPattern(pattern_id)
            return pattern is not None
        except Exception:
            return False

    def _supports_scroll_pattern(self, element):
        """Check if element supports UIA ScrollPattern"""
        try:
            # ScrollPattern ID is 10003
            scroll_pattern = element.GetCurrentPattern(10003)
            return scroll_pattern is not None
        except Exception:
            return False

    def _get_text_readonly_from_textpattern(self, element):
        """Get read-only status from TextPattern/TextPattern2."""
        # Try TextPattern2 (newer) then TextPattern (older)
        # 10024 = TextPattern2, 10014 = TextPattern (UIA IDs)
        for pattern_id in (10024, 10014):
            try:
                pattern = element.GetCurrentPattern(pattern_id)
                if not pattern:
                    continue
                    
                # Try to get caret range or document range
                try:
                    if hasattr(pattern, 'GetCaretRange'):
                        text_range = pattern.GetCaretRange(True)[0]
                    else:
                        text_range = pattern.DocumentRange
                        
                    if text_range:
                        readonly = text_range.GetAttributeValue(UIA_IsReadOnlyAttributeId)
                        if readonly is not None and isinstance(readonly, bool):
                            return readonly
                except Exception:
                    pass
            except Exception:
                pass
        return None  # Unknown

    def _is_editable_element(self, element):
        """Check if a UIA element is an editable text control with enhanced search box detection."""
        try:
            # Import proper constants from loaded module
            from comtypes.gen.UIAutomationClient import (
                UIA_ControlTypePropertyId, UIA_IsEnabledPropertyId, UIA_NamePropertyId,
                UIA_ClassNamePropertyId, UIA_HelpTextPropertyId, UIA_AutomationIdPropertyId,
                UIA_EditControlTypeId, UIA_DocumentControlTypeId, UIA_ComboBoxControlTypeId,
                UIA_PaneControlTypeId, UIA_GroupControlTypeId, UIA_HasKeyboardFocusPropertyId
            )
            
            # Get basic properties
            control_type = element.GetCurrentPropertyValue(UIA_ControlTypePropertyId)
            is_enabled = element.GetCurrentPropertyValue(UIA_IsEnabledPropertyId)
            name = element.GetCurrentPropertyValue(UIA_NamePropertyId) or ""
            class_name = element.GetCurrentPropertyValue(UIA_ClassNamePropertyId) or ""
            help_text = element.GetCurrentPropertyValue(UIA_HelpTextPropertyId) or ""
            automation_id = element.GetCurrentPropertyValue(UIA_AutomationIdPropertyId) or ""
            
            if not is_enabled:
                return False

            # CRITICAL: Must have keyboard focus to be considered active
            has_keyboard_focus = element.GetCurrentPropertyValue(UIA_HasKeyboardFocusPropertyId)
            if not has_keyboard_focus:
                return False

            # Enhanced search box detection by name/text content
            search_indicators = [
                'search', 'find', 'filter', 'query', 'lookup', 'seek',
                'type here', 'enter text', 'search box', 'search field',
                'textbox', 'input', 'edit box', 'type to search', 'search...',
                'search for', 'find in', 'filter by'
            ]
            
            # Check all text properties for search indicators
            all_text = f"{name} {class_name} {help_text} {automation_id}".lower()
            is_search_related = any(indicator in all_text for indicator in search_indicators)
            
            # Primary check: Known text input control types
            text_control_types = (UIA_EditControlTypeId, UIA_DocumentControlTypeId, UIA_ComboBoxControlTypeId)
            if control_type in text_control_types:
                # For Edit controls, check ValuePattern
                if control_type == UIA_EditControlTypeId:
                    if self._supports_pattern(element, 10002):  # ValuePattern
                        # Check if text is read-only via TextPattern
                        readonly = self._get_text_readonly_from_textpattern(element)
                        if readonly is True:
                            return False
                        # Edit controls with ValuePattern are usually editable
                        return True
                    # Edit control without ValuePattern - might still be editable
                    return True

                # For Document controls (contenteditable), be more lenient
                elif control_type == UIA_DocumentControlTypeId:
                    # Check if it has "Text Area" in the name (common for input fields)
                    if "text area" in name.lower() or "textarea" in name.lower():
                        return True
                    
                    # Only consider Document editable if TextPattern explicitly says it's not readonly
                    readonly = self._get_text_readonly_from_textpattern(element)
                    if readonly is False:
                        return True
                    # If readonly status is unknown (None), assume editable for Document with "Text Area" name
                    elif readonly is None and ("text" in name.lower() or "input" in name.lower()):
                        return True
                    else:
                        return False

                # For ComboBox, check if it has editable text
                elif control_type == UIA_ComboBoxControlTypeId:
                    if self._supports_pattern(element, 10002):  # ValuePattern
                        readonly = self._get_text_readonly_from_textpattern(element)
                        return readonly is not True  # Editable unless explicitly readonly
                    return False

            # Secondary check: Search-related elements that might be text inputs
            # Even if they're not traditional edit controls
            elif is_search_related:
                # Check if element supports ValuePattern or TextPattern (indicates text capability)
                if self._supports_pattern(element, 10002) or self._supports_pattern(element, 10014):
                    return True
                    
                # For Pane/Group controls that might contain search boxes
                if control_type in (UIA_PaneControlTypeId, UIA_GroupControlTypeId):
                    # Look for child elements that might be the actual input
                    try:
                        from comtypes.gen.UIAutomationClient import TreeScope_Children
                        uia = self._get_uia()
                        if uia:
                            cond_true = uia.CreateTrueCondition()
                            children = element.FindAll(TreeScope_Children, cond_true)
                            for i in range(min(children.Length, 3)):  # Check first 3 children
                                child = children.GetElement(i)
                                child_type = child.GetCurrentPropertyValue(UIA_ControlTypePropertyId)
                                if child_type in text_control_types:
                                    if self._supports_pattern(child, 10002):  # ValuePattern
                                        return True
                    except Exception:
                        pass

            return False
            
        except Exception:
            return False

    def focused_is_text_editable(self) -> bool:
        """
        Main method to check if the currently focused element is editable text.
        Uses advanced UIA techniques to penetrate web app content.
        """
        if not COMTYPES_AVAILABLE:
            return self._last_result
            
        try:
            uia = self._get_uia()
            if not uia:
                return self._last_result
                
            focused = uia.GetFocusedElement()
            if not focused:
                return self._last_result

            # Direct check on focused element
            if self._is_editable_element(focused):
                # Extra guard: exclude password fields if detectable
                readonly = self._get_text_readonly_from_textpattern(focused)
                if readonly is not None and readonly is True:
                    self._last_result = False
                    return False
                self._last_result = True
                return True

            # For Electron/web apps: focused element might be a wrapper
            # Search immediate children only (not deep descendants)
            try:
                from comtypes.gen.UIAutomationClient import TreeScope_Children, TreeScope_Descendants
                
                cond_true = uia.CreateTrueCondition()
                
                # First: Search immediate children of the focused element
                children = focused.FindAll(TreeScope_Children, cond_true)
                for i in range(min(children.Length, 5)):  # Limit to 5 immediate children
                    element = children.GetElement(i)
                    try:
                        if self._is_editable_element(element):
                            self._last_result = True
                            return True
                    except Exception:
                        continue
                
                # Second: If no direct children, search a bit deeper for search boxes
                # This is more aggressive for apps that deeply nest search fields
                descendants = focused.FindAll(TreeScope_Descendants, cond_true)
                search_found = False
                for i in range(min(descendants.Length, 10)):  # Limit to first 10 descendants
                    element = descendants.GetElement(i)
                    try:
                        # Get element properties for search detection
                        from comtypes.gen.UIAutomationClient import UIA_NamePropertyId, UIA_AutomationIdPropertyId
                        name = element.GetCurrentPropertyValue(UIA_NamePropertyId) or ""
                        automation_id = element.GetCurrentPropertyValue(UIA_AutomationIdPropertyId) or ""
                        
                        # Only look deeper if we find search-related terms
                        search_terms = ['search', 'find', 'filter', 'query', 'textbox']
                        element_text = f"{name} {automation_id}".lower()
                        if any(term in element_text for term in search_terms):
                            if self._is_editable_element(element):
                                print(f"Deep search box found: {name[:30]}")
                                self._last_result = True
                                return True
                                search_found = True
                                break
                    except Exception:
                        continue
                        
            except Exception:
                pass

            # No editable text found
            self._last_result = False
            return False
            
        except Exception as e:
            # Keep last known state on error
            return self._last_result

    def get_scroll_info(self, element=None):
        """Get scroll position information for the focused or specified element - only for genuinely scrollable elements"""
        try:
            if element is None:
                uia = self._get_uia()
                if not uia:
                    return None
                element = uia.GetFocusedElement()
                if not element:
                    return None
            
            # First check if this element should actually be considered scrollable
            if not self._is_genuinely_scrollable(element):
                return None
            
            # Try to get ScrollPattern
            scroll_pattern = element.GetCurrentPattern(10003)  # ScrollPattern ID
            if not scroll_pattern:
                return None
                
            # Get scroll properties
            try:
                horizontal_scroll_percent = scroll_pattern.CurrentHorizontalScrollPercent
                vertical_scroll_percent = scroll_pattern.CurrentVerticalScrollPercent
                horizontal_viewsize = scroll_pattern.CurrentHorizontalViewSize
                vertical_viewsize = scroll_pattern.CurrentVerticalViewSize
                
                return {
                    'can_scroll_horizontally': scroll_pattern.CurrentHorizontallyScrollable,
                    'can_scroll_vertically': scroll_pattern.CurrentVerticallyScrollable,
                    'horizontal_percent': horizontal_scroll_percent,
                    'vertical_percent': vertical_scroll_percent,
                    'horizontal_viewsize': horizontal_viewsize,
                    'vertical_viewsize': vertical_viewsize,
                    'at_top': vertical_scroll_percent <= 0.0,
                    'at_bottom': vertical_scroll_percent >= 100.0,
                    'at_left': horizontal_scroll_percent <= 0.0,
                    'at_right': horizontal_scroll_percent >= 100.0
                }
            except Exception:
                # If we can't get detailed scroll info, return None (don't assume it's scrollable)
                return None
                
        except Exception:
            return None

    def _is_genuinely_scrollable(self, element):
        """Check if an element is genuinely scrollable (not just a button with scroll pattern)"""
        try:
            from comtypes.gen.UIAutomationClient import (
                UIA_ControlTypePropertyId, UIA_NamePropertyId, UIA_ClassNamePropertyId,
                UIA_ListControlTypeId, UIA_DataGridControlTypeId, UIA_TreeControlTypeId,
                UIA_DocumentControlTypeId, UIA_PaneControlTypeId, UIA_GroupControlTypeId,
                UIA_ButtonControlTypeId, UIA_MenuItemControlTypeId, UIA_HyperlinkControlTypeId,
                UIA_TabItemControlTypeId, UIA_CheckBoxControlTypeId, UIA_RadioButtonControlTypeId
            )
            
            control_type = element.GetCurrentPropertyValue(UIA_ControlTypePropertyId)
            name = element.GetCurrentPropertyValue(UIA_NamePropertyId) or ""
            class_name = element.GetCurrentPropertyValue(UIA_ClassNamePropertyId) or ""
            
            # Exclude control types that should never be considered scrollable containers
            non_scrollable_types = [
                UIA_ButtonControlTypeId, UIA_MenuItemControlTypeId, UIA_HyperlinkControlTypeId,
                UIA_TabItemControlTypeId, UIA_CheckBoxControlTypeId, UIA_RadioButtonControlTypeId
            ]
            
            if control_type in non_scrollable_types:
                return False
                
            # Only consider these control types as potentially scrollable
            potentially_scrollable_types = [
                UIA_ListControlTypeId, UIA_DataGridControlTypeId, UIA_TreeControlTypeId,
                UIA_DocumentControlTypeId, UIA_PaneControlTypeId, UIA_GroupControlTypeId
            ]
            
            if control_type not in potentially_scrollable_types:
                return False
                
            # Additional checks for genuinely scrollable content
            name_lower = name.lower()
            class_lower = class_name.lower()
            
            # Look for explicit scrollable indicators
            scrollable_indicators = [
                'list', 'grid', 'tree', 'scroll', 'content', 'document', 'view',
                'listview', 'treeview', 'datagrid', 'scrollpane', 'scrollarea'
            ]
            
            # Must have scrollable indicators OR be a known scrollable control type
            if control_type in [UIA_ListControlTypeId, UIA_DataGridControlTypeId, UIA_TreeControlTypeId]:
                return True  # These are inherently scrollable
                
            # For Pane/Group/Document, require explicit indicators
            if any(indicator in name_lower for indicator in scrollable_indicators) or \
               any(indicator in class_lower for indicator in scrollable_indicators):
                return True
                
            return False
            
        except Exception:
            return False

    def get_element_context(self):
        """Determine the context mode based on the focused element type with enhanced scrollable detection"""
        try:
            uia = self._get_uia()
            if not uia:
                return {'mode': 'tab', 'reason': 'No UIA'}
            
            focused_element = uia.GetFocusedElement()
            if not focused_element:
                return {'mode': 'tab', 'reason': 'No focused element'}
            
            from comtypes.gen.UIAutomationClient import (
                UIA_ControlTypePropertyId, UIA_NamePropertyId, UIA_ClassNamePropertyId,
                UIA_EditControlTypeId, UIA_DocumentControlTypeId, UIA_ComboBoxControlTypeId,
                UIA_ListControlTypeId, UIA_DataGridControlTypeId, UIA_TreeControlTypeId,
                UIA_ButtonControlTypeId, UIA_CheckBoxControlTypeId, UIA_MenuItemControlTypeId,
                UIA_HyperlinkControlTypeId, UIA_TabItemControlTypeId
            )
            
            control_type = focused_element.GetCurrentPropertyValue(UIA_ControlTypePropertyId)
            name = focused_element.GetCurrentPropertyValue(UIA_NamePropertyId) or ""
            class_name = focused_element.GetCurrentPropertyValue(UIA_ClassNamePropertyId) or ""
            
            # Priority 1: Check if it's a text input (MORSE mode)
            if self._is_editable_element(focused_element):
                return {
                    'mode': 'morse',
                    'reason': 'Editable text field',
                    'control_type': control_type,
                    'name': name[:50],  # Truncate for display
                    'class_name': class_name,
                    'scroll_info': None
                }
            
            # Priority 2: Check if it's explicitly scrollable content (SCROLL mode)
            is_scrollable = self._is_scrollable_element(focused_element, control_type, name, class_name)
            if is_scrollable:
                # Get scroll information for boundary detection
                scroll_info = self.get_scroll_info(focused_element)
                return {
                    'mode': 'scroll',
                    'reason': 'Scrollable element detected',
                    'control_type': control_type,
                    'name': name[:50],
                    'class_name': class_name,
                    'scroll_info': scroll_info
                }
            
            # Priority 3: Default to TAB mode for all other elements
            return {
                'mode': 'tab',
                'reason': 'Default (Tab navigation)',
                'control_type': control_type,
                'name': name[:50],
                'class_name': class_name,
                'scroll_info': None
            }
            
        except Exception as e:
            return {'mode': 'tab', 'reason': f'Error: {str(e)[:50]}', 'scroll_info': None}

    def _is_scrollable_element(self, element, control_type, name, class_name):
        """Check if an element is scrollable content that should use SCROLL mode - ENHANCED"""
        try:
            from comtypes.gen.UIAutomationClient import (
                UIA_ListControlTypeId, UIA_DataGridControlTypeId, UIA_TreeControlTypeId,
                UIA_PaneControlTypeId, UIA_GroupControlTypeId, UIA_WindowControlTypeId
            )
            
            # Priority 1: Explicit list/grid/tree controls
            scrollable_types = [UIA_ListControlTypeId, UIA_DataGridControlTypeId, UIA_TreeControlTypeId]
            if control_type in scrollable_types:
                return True
            
            # Priority 2: Check for ScrollPattern support
            if self._supports_scroll_pattern(element):
                # Additional checks for common container types that might be scrollable
                container_types = [UIA_PaneControlTypeId, UIA_GroupControlTypeId, UIA_WindowControlTypeId]
                if control_type in container_types:
                    return True
            
            # Priority 3: Name and class-based detection (expanded patterns)
            name_lower = name.lower()
            class_lower = class_name.lower()
            
            # Expanded patterns for scrollable elements
            scrollable_patterns = [
                # General list patterns
                'list', 'playlist', 'song list', 'track list', 'file list', 'folder list',
                'message list', 'chat list', 'conversation list', 'contact list',
                # View patterns
                'list view', 'grid view', 'icon view', 'tile view', 'details view',
                'playlist view', 'library view', 'browser view',
                # Scroll-specific patterns
                'scroll', 'scrollable', 'scrollpane', 'scrollarea', 'scrollview',
                # Control patterns
                'listview', 'treeview', 'datagrid', 'listbox', 'combobox list',
                # Content patterns
                'content area', 'main content', 'content pane', 'results',
                'search results', 'browse results', 'feed', 'timeline',
                # Application-specific patterns
                'spotify', 'music', 'library', 'browse', 'discover', 'queue',
                'explorer', 'finder', 'files', 'documents', 'downloads'
            ]
            
            if any(pattern in name_lower for pattern in scrollable_patterns) or \
               any(pattern in class_lower for pattern in scrollable_patterns):
                return True
                
            return False
            
        except Exception:
            return False

    def get_debug_info(self) -> dict:
        """Get debug information about the focused element."""
        if not COMTYPES_AVAILABLE:
            return {"error": "comtypes not available"}
            
        try:
            uia = self._get_uia()
            if not uia:
                return {"error": "UIA not available"}
                
            focused = uia.GetFocusedElement()
            if not focused:
                return {"error": "no focused element"}
                
            try:
                # Import UIA property constants with fallbacks for missing ones
                def safe_import_constant(module, name, fallback_value):
                    try:
                        return getattr(module, name)
                    except AttributeError:
                        return fallback_value
                
                from comtypes.gen import UIAutomationClient
                
                # Basic identification properties (these should always be available)
                UIA_ControlTypePropertyId = safe_import_constant(UIAutomationClient, 'UIA_ControlTypePropertyId', 30003)
                UIA_NamePropertyId = safe_import_constant(UIAutomationClient, 'UIA_NamePropertyId', 30005)
                UIA_ClassNamePropertyId = safe_import_constant(UIAutomationClient, 'UIA_ClassNamePropertyId', 30012)
                UIA_AutomationIdPropertyId = safe_import_constant(UIAutomationClient, 'UIA_AutomationIdPropertyId', 30011)
                UIA_LocalizedControlTypePropertyId = safe_import_constant(UIAutomationClient, 'UIA_LocalizedControlTypePropertyId', 30004)
                UIA_ProcessIdPropertyId = safe_import_constant(UIAutomationClient, 'UIA_ProcessIdPropertyId', 30002)
                UIA_NativeWindowHandlePropertyId = safe_import_constant(UIAutomationClient, 'UIA_NativeWindowHandlePropertyId', 30020)
                
                # State and capability properties
                UIA_IsEnabledPropertyId = safe_import_constant(UIAutomationClient, 'UIA_IsEnabledPropertyId', 30010)
                UIA_HasKeyboardFocusPropertyId = safe_import_constant(UIAutomationClient, 'UIA_HasKeyboardFocusPropertyId', 30008)
                UIA_IsKeyboardFocusablePropertyId = safe_import_constant(UIAutomationClient, 'UIA_IsKeyboardFocusablePropertyId', 30009)
                UIA_IsOffscreenPropertyId = safe_import_constant(UIAutomationClient, 'UIA_IsOffscreenPropertyId', 30022)
                UIA_IsPasswordPropertyId = safe_import_constant(UIAutomationClient, 'UIA_IsPasswordPropertyId', 30019)
                UIA_IsRequiredForFormPropertyId = safe_import_constant(UIAutomationClient, 'UIA_IsRequiredForFormPropertyId', 30025)
                UIA_IsControlElementPropertyId = safe_import_constant(UIAutomationClient, 'UIA_IsControlElementPropertyId', 30017)
                UIA_IsContentElementPropertyId = safe_import_constant(UIAutomationClient, 'UIA_IsContentElementPropertyId', 30018)
                
                # Text and input properties
                UIA_HelpTextPropertyId = safe_import_constant(UIAutomationClient, 'UIA_HelpTextPropertyId', 30013)
                UIA_AcceleratorKeyPropertyId = safe_import_constant(UIAutomationClient, 'UIA_AcceleratorKeyPropertyId', 30006)
                UIA_AccessKeyPropertyId = safe_import_constant(UIAutomationClient, 'UIA_AccessKeyPropertyId', 30007)
                UIA_ValueValuePropertyId = safe_import_constant(UIAutomationClient, 'UIA_ValueValuePropertyId', 30045)
                UIA_IsReadOnlyPropertyId = safe_import_constant(UIAutomationClient, 'UIA_IsReadOnlyPropertyId', 30046)
                
                # Layout and appearance properties
                UIA_BoundingRectanglePropertyId = safe_import_constant(UIAutomationClient, 'UIA_BoundingRectanglePropertyId', 30001)
                UIA_OrientationPropertyId = safe_import_constant(UIAutomationClient, 'UIA_OrientationPropertyId', 30023)
                UIA_CulturePropertyId = safe_import_constant(UIAutomationClient, 'UIA_CulturePropertyId', 30015)
                UIA_ItemTypePropertyId = safe_import_constant(UIAutomationClient, 'UIA_ItemTypePropertyId', 30021)
                UIA_ItemStatusPropertyId = safe_import_constant(UIAutomationClient, 'UIA_ItemStatusPropertyId', 30026)
                
                # System properties
                UIA_ProviderDescriptionPropertyId = safe_import_constant(UIAutomationClient, 'UIA_ProviderDescriptionPropertyId', 30014)
                UIA_FrameworkIdPropertyId = safe_import_constant(UIAutomationClient, 'UIA_FrameworkIdPropertyId', 30024)
                
                # Grid and table properties
                UIA_GridRowCountPropertyId = safe_import_constant(UIAutomationClient, 'UIA_GridRowCountPropertyId', 30062)
                UIA_GridColumnCountPropertyId = safe_import_constant(UIAutomationClient, 'UIA_GridColumnCountPropertyId', 30063)
                UIA_GridItemRowPropertyId = safe_import_constant(UIAutomationClient, 'UIA_GridItemRowPropertyId', 30064)
                UIA_GridItemColumnPropertyId = safe_import_constant(UIAutomationClient, 'UIA_GridItemColumnPropertyId', 30065)
                UIA_GridItemRowSpanPropertyId = safe_import_constant(UIAutomationClient, 'UIA_GridItemRowSpanPropertyId', 30066)
                UIA_GridItemColumnSpanPropertyId = safe_import_constant(UIAutomationClient, 'UIA_GridItemColumnSpanPropertyId', 30067)
                
                # Helper function to safely get property values
                def safe_get_property(prop_id, default=""):
                    try:
                        value = focused.GetCurrentPropertyValue(prop_id)
                        return value if value is not None else default
                    except:
                        return default
                
                # Basic identification properties
                control_type = safe_get_property(UIA_ControlTypePropertyId, 0)
                name = safe_get_property(UIA_NamePropertyId, "")
                class_name = safe_get_property(UIA_ClassNamePropertyId, "")
                automation_id = safe_get_property(UIA_AutomationIdPropertyId, "")
                localized_control_type = safe_get_property(UIA_LocalizedControlTypePropertyId, "")
                process_id = safe_get_property(UIA_ProcessIdPropertyId, 0)
                native_window_handle = safe_get_property(UIA_NativeWindowHandlePropertyId, 0)
                framework_id = safe_get_property(UIA_FrameworkIdPropertyId, "")
                provider_description = safe_get_property(UIA_ProviderDescriptionPropertyId, "")
                
                # State and capability properties
                is_enabled = safe_get_property(UIA_IsEnabledPropertyId, False)
                has_keyboard_focus = safe_get_property(UIA_HasKeyboardFocusPropertyId, False)
                is_keyboard_focusable = safe_get_property(UIA_IsKeyboardFocusablePropertyId, False)
                is_offscreen = safe_get_property(UIA_IsOffscreenPropertyId, False)
                is_password = safe_get_property(UIA_IsPasswordPropertyId, False)
                is_required_for_form = safe_get_property(UIA_IsRequiredForFormPropertyId, False)
                is_control_element = safe_get_property(UIA_IsControlElementPropertyId, False)
                is_content_element = safe_get_property(UIA_IsContentElementPropertyId, False)
                
                # Text and input properties
                help_text = safe_get_property(UIA_HelpTextPropertyId, "")
                accelerator_key = safe_get_property(UIA_AcceleratorKeyPropertyId, "")
                access_key = safe_get_property(UIA_AccessKeyPropertyId, "")
                is_readonly = safe_get_property(UIA_IsReadOnlyPropertyId, None)
                
                # Layout and appearance properties
                bounding_rect = safe_get_property(UIA_BoundingRectanglePropertyId, None)
                orientation = safe_get_property(UIA_OrientationPropertyId, "")
                culture = safe_get_property(UIA_CulturePropertyId, "")
                item_type = safe_get_property(UIA_ItemTypePropertyId, "")
                item_status = safe_get_property(UIA_ItemStatusPropertyId, "")
                
                # Grid and table properties
                grid_row_count = safe_get_property(UIA_GridRowCountPropertyId, 0)
                grid_column_count = safe_get_property(UIA_GridColumnCountPropertyId, 0)
                grid_item_row = safe_get_property(UIA_GridItemRowPropertyId, -1)
                grid_item_column = safe_get_property(UIA_GridItemColumnPropertyId, -1)
                grid_item_row_span = safe_get_property(UIA_GridItemRowSpanPropertyId, 0)
                grid_item_column_span = safe_get_property(UIA_GridItemColumnSpanPropertyId, 0)
                
                # Check ALL UIA patterns
                has_invoke_pattern = self._supports_pattern(focused, 10000)        # InvokePattern
                has_selection_pattern = self._supports_pattern(focused, 10001)     # SelectionPattern
                has_value_pattern = self._supports_pattern(focused, 10002)         # ValuePattern
                has_range_value_pattern = self._supports_pattern(focused, 10003)   # RangeValuePattern
                has_scroll_pattern = self._supports_pattern(focused, 10004)        # ScrollPattern
                has_expand_collapse_pattern = self._supports_pattern(focused, 10005) # ExpandCollapsePattern
                has_grid_pattern = self._supports_pattern(focused, 10006)          # GridPattern
                has_grid_item_pattern = self._supports_pattern(focused, 10007)     # GridItemPattern
                has_multipleview_pattern = self._supports_pattern(focused, 10008)  # MultipleViewPattern
                has_window_pattern = self._supports_pattern(focused, 10009)        # WindowPattern
                has_selection_item_pattern = self._supports_pattern(focused, 10010) # SelectionItemPattern
                has_dock_pattern = self._supports_pattern(focused, 10011)          # DockPattern
                has_table_pattern = self._supports_pattern(focused, 10012)         # TablePattern
                has_table_item_pattern = self._supports_pattern(focused, 10013)    # TableItemPattern
                has_text_pattern = self._supports_pattern(focused, 10014)          # TextPattern
                has_toggle_pattern = self._supports_pattern(focused, 10015)        # TogglePattern
                has_transform_pattern = self._supports_pattern(focused, 10016)     # TransformPattern
                has_scroll_item_pattern = self._supports_pattern(focused, 10017)   # ScrollItemPattern
                has_legacy_iaccessible_pattern = self._supports_pattern(focused, 10018) # LegacyIAccessiblePattern
                has_item_container_pattern = self._supports_pattern(focused, 10019) # ItemContainerPattern
                has_virtualized_item_pattern = self._supports_pattern(focused, 10020) # VirtualizedItemPattern
                has_synchronized_input_pattern = self._supports_pattern(focused, 10021) # SynchronizedInputPattern
                
                readonly = self._get_text_readonly_from_textpattern(focused)
                
                # Get scroll information
                scroll_info = self.get_scroll_info(focused)
                
                # Try to get current value if it has ValuePattern
                current_value = ""
                try:
                    if has_value_pattern:
                        value_pattern = focused.GetCurrentPattern(10002)
                        if value_pattern:
                            current_value = value_pattern.CurrentValue or ""
                    else:
                        # Try TextPattern as alternative
                        if has_text_pattern:
                            text_pattern = focused.GetCurrentPattern(10014)
                            if text_pattern:
                                document_range = text_pattern.DocumentRange
                                if document_range:
                                    current_value = document_range.GetText(-1) or ""
                except Exception as e:
                    pass
                
                return {
                    # Basic identification
                    "name": str(name) if name else "",
                    "class_name": str(class_name) if class_name else "",
                    "control_type": control_type,
                    "control_type_name": self._get_control_type_name(control_type),
                    "automation_id": str(automation_id) if automation_id else "",
                    "localized_control_type": str(localized_control_type) if localized_control_type else "",
                    
                    # System information
                    "process_id": process_id,
                    "native_window_handle": native_window_handle,
                    "framework_id": str(framework_id) if framework_id else "",
                    "provider_description": str(provider_description) if provider_description else "",
                    
                    # State and capabilities
                    "is_enabled": is_enabled,
                    "has_keyboard_focus": has_keyboard_focus,
                    "is_keyboard_focusable": is_keyboard_focusable,
                    "is_offscreen": is_offscreen,
                    "is_password": is_password,
                    "is_required_for_form": is_required_for_form,
                    "is_control_element": is_control_element,
                    "is_content_element": is_content_element,
                    
                    # Text and input
                    "help_text": str(help_text) if help_text else "",
                    "accelerator_key": str(accelerator_key) if accelerator_key else "",
                    "access_key": str(access_key) if access_key else "",
                    "current_value": str(current_value),
                    "is_readonly": is_readonly,
                    "text_readonly": readonly,
                    "is_text_editable": self.focused_is_text_editable(),
                    
                    # Layout and appearance
                    "bounding_rect": bounding_rect,
                    "orientation": str(orientation) if orientation else "",
                    "culture": str(culture) if culture else "",
                    "item_type": str(item_type) if item_type else "",
                    "item_status": str(item_status) if item_status else "",
                    
                    # Grid and table information
                    "grid_row_count": grid_row_count if grid_row_count > 0 else None,
                    "grid_column_count": grid_column_count if grid_column_count > 0 else None,
                    "grid_item_row": grid_item_row if grid_item_row >= 0 else None,
                    "grid_item_column": grid_item_column if grid_item_column >= 0 else None,
                    "grid_item_row_span": grid_item_row_span if grid_item_row_span > 0 else None,
                    "grid_item_column_span": grid_item_column_span if grid_item_column_span > 0 else None,
                    
                    # All UIA patterns
                    "has_invoke_pattern": has_invoke_pattern,
                    "has_selection_pattern": has_selection_pattern,
                    "has_value_pattern": has_value_pattern,
                    "has_range_value_pattern": has_range_value_pattern,
                    "has_scroll_pattern": has_scroll_pattern,
                    "has_expand_collapse_pattern": has_expand_collapse_pattern,
                    "has_grid_pattern": has_grid_pattern,
                    "has_grid_item_pattern": has_grid_item_pattern,
                    "has_multipleview_pattern": has_multipleview_pattern,
                    "has_window_pattern": has_window_pattern,
                    "has_selection_item_pattern": has_selection_item_pattern,
                    "has_dock_pattern": has_dock_pattern,
                    "has_table_pattern": has_table_pattern,
                    "has_table_item_pattern": has_table_item_pattern,
                    "has_text_pattern": has_text_pattern,
                    "has_toggle_pattern": has_toggle_pattern,
                    "has_transform_pattern": has_transform_pattern,
                    "has_scroll_item_pattern": has_scroll_item_pattern,
                    "has_legacy_iaccessible_pattern": has_legacy_iaccessible_pattern,
                    "has_item_container_pattern": has_item_container_pattern,
                    "has_virtualized_item_pattern": has_virtualized_item_pattern,
                    "has_synchronized_input_pattern": has_synchronized_input_pattern,
                    
                    # Scroll information
                    "scroll_info": scroll_info
                }
            except Exception as e:
                return {"error": f"Property access failed: {e}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _get_control_type_name(self, control_type):
        """Convert control type ID to readable name."""
        control_type_names = {
            50000: "Button", 50001: "Calendar", 50002: "CheckBox", 50003: "ComboBox",
            50004: "Edit", 50005: "Hyperlink", 50006: "Image", 50007: "ListItem",
            50008: "List", 50009: "Menu", 50010: "MenuBar", 50011: "MenuItem",
            50012: "ProgressBar", 50013: "RadioButton", 50014: "ScrollBar",
            50015: "Slider", 50016: "Spinner", 50017: "StatusBar", 50018: "Tab",
            50019: "TabItem", 50020: "Text", 50021: "ToolBar", 50022: "ToolTip",
            50023: "Tree", 50024: "TreeItem", 50025: "Custom", 50026: "Group",
            50027: "Thumb", 50028: "DataGrid", 50029: "DataItem", 50030: "Document",
            50031: "SplitButton", 50032: "Window", 50033: "Pane", 50034: "Header",
            50035: "HeaderItem", 50036: "Table", 50037: "TitleBar", 50038: "Separator"
        }
        return control_type_names.get(control_type, f"Unknown({control_type})")

    def __del__(self):
        """Cleanup COM when object is destroyed"""
        if hasattr(self, '_com_initialized') and self._com_initialized:
            try:
                import comtypes
                comtypes.CoUninitialize()
            except:
                pass