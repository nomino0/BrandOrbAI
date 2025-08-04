"use client"

import * as React from "react"
import { useState, useEffect } from "react"
import { useTheme } from "next-themes"
import Image from "next/image"
import Link from "next/link"
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
      title: "Stage 2: SWOT Analysis",
      url: "/dashboard/critical-report",
      icon: IconFileText,
      status: "current",
      progress: 0,
      items: [
        {
          title: "Strengths Analysis",
          url: "/dashboard/critical-report/1",
          status: "locked",
        },
        {
          title: "Weaknesses Analysis",
          url: "/dashboard/critical-report/2",
          status: "locked",
        },
        {
          title: "Opportunities Analysis",
          url: "/dashboard/critical-report/3",
          status: "locked",
        },
        {
          title: "Threats Analysis",
          url: "/dashboard/critical-report/4",
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
  const [mounted, setMounted] = useState(false)
  const { resolvedTheme } = useTheme()

  useEffect(() => {
    setMounted(true)
  }, [])

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <Link href="/dashboard" className="flex items-center space-x-2">
                <div className="relative h-9 w-auto">
                  {!mounted ? (
                    // Placeholder during hydration
                    <div className="h-9 w-[138px] bg-sidebar-accent animate-pulse rounded" />
                  ) : (
                    <Image
                      src={resolvedTheme === 'dark' ? '/logo/dark.svg' : '/logo/white.svg'}
                      alt="BrandOrb AI"
                      width={138}
                      height={36}
                      className="h-9 w-[138px] object-contain"
                      priority
                    />
                  )}
                </div>
              </Link>
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
