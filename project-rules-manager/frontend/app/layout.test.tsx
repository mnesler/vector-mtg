import { render, screen } from '@testing-library/react'
import RootLayout from './layout'

// Mock child components to avoid rendering issues
jest.mock('../components/AppBar', () => {
  return function MockAppBar({ onMenuClick }: any) {
    return <div data-testid="mock-appbar">AppBar</div>
  }
})

jest.mock('../components/NavigationDrawer', () => {
  return function MockNavigationDrawer({ isOpen, onClose }: any) {
    return <div data-testid="mock-drawer">NavigationDrawer</div>
  }
})

describe('RootLayout', () => {
  it('renders children correctly', () => {
    const { container } = render(
      <RootLayout>
        <div data-testid="test-child">Test Content</div>
      </RootLayout>
    )

    expect(screen.getByTestId('test-child')).toBeInTheDocument()
    expect(screen.getByText('Test Content')).toBeInTheDocument()
  })

  it('renders AppBar component', () => {
    render(
      <RootLayout>
        <div>Test</div>
      </RootLayout>
    )

    expect(screen.getByTestId('mock-appbar')).toBeInTheDocument()
  })

  it('renders NavigationDrawer component', () => {
    render(
      <RootLayout>
        <div>Test</div>
      </RootLayout>
    )

    expect(screen.getByTestId('mock-drawer')).toBeInTheDocument()
  })
})
