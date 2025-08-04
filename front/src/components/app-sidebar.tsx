"use client"

import * as React from "react"
import {
  IconCheck,
  IconCircle,
  IconLoader,
  IconLock,
  IconBulb,
  IconFileText,
  IconTable,
  IconTarget,
  IconCalendar,
} from "@tabler/icons-react"

import { NavMain } from "@/components/nav-main"
import { NavUser } from "@/components/nav-user"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"

const data = {
  user: {
    name: "BrandOrb User",
    email: "user@brandorb.ai",
    avatar: "/avatars/user.jpg",
  },
  navMain: [
    {
      title: "Stage 1: Ideation",
      url: "/dashboard/ideation",
      icon: IconBulb,
      isActive: true,
      status: "completed",
      items: [],
    },
    {
      title: "Stage 2: Critical Report",
      url: "/dashboard/critical-report",
      icon: IconFileText,
      status: "current",
      progress: 0,
      items: [
        {
          title: "Market Research",
          url: "/dashboard/critical-report/1",
          status: "locked",
        },
        {
          title: "Opportunities",
          url: "/dashboard/critical-report/2",
          status: "locked",
        },
        {
          title: "Value Proposition",
          url: "/dashboard/critical-report/3",
          status: "locked",
        },
        {
          title: "Competitor Analysis",
          url: "/dashboard/critical-report/4",
          status: "locked",
        },
        {
          title: "Revenue Model",
          url: "/dashboard/critical-report/5",
          status: "locked",
        },
        {
          title: "Legal Assessment",
          url: "/dashboard/critical-report/6",
          status: "locked",
        },
        {
          title: "Marketing Strategy",
          url: "/dashboard/critical-report/7",
          status: "locked",
        },
        {
          title: "Financial Projections",
          url: "/dashboard/critical-report/8",
          status: "locked",
        },
        {
          title: "Implementation Plan",
          url: "/dashboard/critical-report/9",
          status: "locked",
        },
      ],
    },
    {
      title: "Stage 3: BMC",
      url: "/dashboard/bmc",
      icon: IconTable,
      status: "locked",
      items: [],
    },
    {
      title: "Stage 4: Milestones",
      url: "/dashboard/milestones",
      icon: IconTarget,
      status: "locked",
      items: [],
    },
    {
      title: "Roadmap & Calendar",
      url: "/dashboard/roadmap",
      icon: IconCalendar,
      status: "locked",
      items: [],
    },
  ],
}

function getStatusIcon(status: string, progress?: number) {
  switch (status) {
    case "completed":
      return <IconCheck className="h-4 w-4 text-green-600" />
    case "current":
      return <IconLoader className="h-4 w-4 text-blue-600 animate-spin" />
    case "locked":
      return <IconLock className="h-4 w-4 text-gray-400" />
    default:
      return <IconCircle className="h-4 w-4 text-gray-400" />
  }
}

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <a href="/dashboard">
                <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                  <IconBulb className="size-4" />
                </div>
                <div className="grid flex-1 text-left text-sm leading-tight">
                  <span className="truncate font-semibold">BrandOrbAI</span>
                  <span className="truncate text-xs">Product Development</span>
                </div>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={data.user} />
      </SidebarFooter>
    </Sidebar>
  )
}
