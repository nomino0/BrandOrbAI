"use client"

import { IconCheck, IconLoader, IconLock, IconChevronRight, type Icon } from "@tabler/icons-react"
import { useState } from "react"

import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from "@/components/ui/sidebar"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"

function getStatusIcon(status: string) {
  switch (status) {
    case "completed":
      return <IconCheck className="h-4 w-4 text-green-600" />
    case "current":
      return <IconLoader className="h-4 w-4 text-blue-600" />
    case "locked":
      return <IconLock className="h-4 w-4 text-gray-400" />
    default:
      return null
  }
}

export function NavMain({
  items,
}: {
  items: {
    title: string
    url: string
    icon?: Icon
    status?: string
    progress?: number
    isActive?: boolean
    items?: {
      title: string
      url: string
      status?: string
    }[]
  }[]
}) {
  const [openItems, setOpenItems] = useState<Record<string, boolean>>({
    "Stage 2: SWOT Analysis": true, // Keep SWOT analysis expanded by default
  })

  const toggleItem = (title: string) => {
    setOpenItems(prev => ({
      ...prev,
      [title]: !prev[title]
    }))
  }

  return (
    <SidebarGroup>
      <SidebarGroupContent>
        <SidebarMenu>
          {items.map((item) => (
            <Collapsible
              key={item.title}
              open={openItems[item.title]}
              onOpenChange={() => toggleItem(item.title)}
            >
              <SidebarMenuItem>
                <CollapsibleTrigger asChild>
                  <SidebarMenuButton 
                    tooltip={item.title}
                    className={`w-full ${item.isActive ? 'bg-sidebar-accent text-sidebar-accent-foreground' : ''}`}
                    asChild
                  >
                    <a href={item.url} className="flex items-center gap-2 w-full">
                      <div className="flex items-center gap-2 flex-1">
                        {item.icon && <item.icon className="h-4 w-4" />}
                        <span className="truncate">{item.title}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        {getStatusIcon(item.status || "")}
                        {item.items && item.items.length > 0 && (
                          <IconChevronRight 
                            className={`h-3 w-3 transition-transform ${
                              openItems[item.title] ? 'rotate-90' : ''
                            }`} 
                          />
                        )}
                      </div>
                    </a>
                  </SidebarMenuButton>
                </CollapsibleTrigger>
                
                {item.items && item.items.length > 0 && (
                  <CollapsibleContent>
                    <SidebarMenuSub>
                      {item.items.map((subItem, index) => (
                        <SidebarMenuSubItem key={subItem.title}>
                          <SidebarMenuSubButton asChild>
                            <a href={subItem.url} className="flex items-center gap-2 w-full">
                              <span className="text-xs text-muted-foreground">{index + 1}.</span>
                              <span className="truncate flex-1">{subItem.title}</span>
                              {getStatusIcon(subItem.status || "")}
                            </a>
                          </SidebarMenuSubButton>
                        </SidebarMenuSubItem>
                      ))}
                    </SidebarMenuSub>
                  </CollapsibleContent>
                )}
              </SidebarMenuItem>
            </Collapsible>
          ))}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  )
}
