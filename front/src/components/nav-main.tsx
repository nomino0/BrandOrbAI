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
        <SidebarMenu className="gap-2">
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
                    className={`w-full h-12 px-3 rounded-lg transition-all duration-200 hover:bg-sidebar-accent/50 ${
                      item.isActive 
                        ? 'bg-white dark:bg-white text-gray-900 shadow-sm border border-sidebar-border' 
                        : ''
                    }`}
                    asChild
                  >
                    <a href={item.url} className="flex items-center gap-3 w-full">
                      <div className="flex items-center gap-3 flex-1">
                        {item.icon && <item.icon className="h-5 w-5 shrink-0" />}
                        <span className="truncate font-medium">{item.title}</span>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        {getStatusIcon(item.status || "")}
                        {item.items && item.items.length > 0 && (
                          <IconChevronRight 
                            className={`h-4 w-4 transition-transform duration-200 ${
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
                    <SidebarMenuSub className="ml-6 mt-2 border-l border-sidebar-border/30">
                      {item.items.map((subItem, index) => (
                        <SidebarMenuSubItem key={subItem.title} className="pl-4 py-1">
                          <SidebarMenuSubButton asChild>
                            <a href={subItem.url} className="flex items-center gap-3 w-full h-10 px-3 rounded-md transition-all duration-200 hover:bg-sidebar-accent/30 group">
                              <span className="text-xs text-muted-foreground group-hover:text-foreground transition-colors">
                                {index + 1}.
                              </span>
                              <span className="truncate flex-1 text-sm group-hover:text-foreground transition-colors">
                                {subItem.title}
                              </span>
                              <div className="shrink-0">
                                {getStatusIcon(subItem.status || "")}
                              </div>
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
